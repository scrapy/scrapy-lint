from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ruamel.yaml import YAML, CommentedMap
from ruamel.yaml.error import YAMLError

from .context import Context, Project
from .errors import CloudError, InputFileError
from .finders.settings import SettingChecker
from .finders.zyte import _value_position
from .issues import UNREACHABLE_PROJECT, Issue

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable

    from .issues import Pos

_DASH_ENDPOINT = "https://app.zyte.com/api/"
_STORAGE_ENDPOINT = "https://storage.scrapinghub.com/"
_API_KEY_ENV_VARS = ("SHUB_APIKEY", "SH_APIKEY")
_MAX_WORKERS = 8


@dataclass
class _CloudProject:
    target: str
    project_id: int
    pos: Pos
    apikey: str


@dataclass
class _Group:
    """Projects that a single Scrapy Cloud client can check."""

    api_key: str
    projects: list[_CloudProject] = field(default_factory=list)


def _global_config() -> dict[str, Any]:
    path = Path.home() / ".scrapinghub.yml"
    if not path.exists():
        return {}
    try:
        data = YAML(typ="safe").load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, YAMLError):
        return {}
    return data if isinstance(data, dict) else {}


def _str_mapping(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {
        key: item
        for key, item in value.items()
        if isinstance(key, str) and isinstance(item, str)
    }


def _check_endpoints(data: CommentedMap) -> None:
    for config in (_global_config(), data):
        url = _str_mapping(config.get("endpoints")).get("default")
        if url is not None and url.rstrip("/") != _DASH_ENDPOINT.rstrip("/"):
            raise CloudError(
                f"the default endpoint is set to {url}, and only "
                f"{_DASH_ENDPOINT} is supported",
            )


def _api_keys(data: CommentedMap) -> dict[str, str]:
    """Return the API keys by target name.

    They are read from :file:`~/.scrapinghub.yml` and then from the
    :file:`scrapinghub.yml` file of the project, the same way shub reads them.
    """
    apikeys: dict[str, str] = {}
    for config in (_global_config(), data):
        apikeys.update(_str_mapping(config.get("apikeys")))
    for variable in _API_KEY_ENV_VARS:
        key = os.environ.get(variable)
        if key:
            apikeys["default"] = key
            break
    return apikeys


def _client(api_key: str) -> Any:
    try:
        from scrapinghub import ScrapinghubClient  # noqa: PLC0415
    except ImportError:
        raise CloudError(
            "the cloud command requires python-scrapinghub; install it with "
            "`pip install scrapy-lint[scrapy-cloud]`",
        ) from None
    return ScrapinghubClient(
        auth=api_key,
        dash_endpoint=_DASH_ENDPOINT,
        endpoint=_STORAGE_ENDPOINT,
    )


def _parse_project(target: str, value: Any, pos: Pos) -> _CloudProject | None:
    """Return the project that a ``projects`` entry of scrapinghub.yml declares."""
    endpoint = apikey = None
    if isinstance(value, CommentedMap):
        endpoint = value.get("endpoint")
        apikey = value.get("apikey")
        value = value.get("id")
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        return None
    if isinstance(value, str) and "/" in value:
        endpoint, _, value = value.partition("/")
    if endpoint is not None and endpoint != "default":
        raise CloudError(
            f"project {target} uses the {endpoint} endpoint, and only "
            f"{_DASH_ENDPOINT} is supported",
        )
    try:
        project_id = int(value)
    except ValueError:
        return None
    apikey = apikey if isinstance(apikey, str) else "default"
    return _CloudProject(target, project_id, pos, apikey)


def _iter_projects(data: CommentedMap) -> Generator[_CloudProject]:
    projects = data.get("projects")
    if not isinstance(projects, CommentedMap):
        return
    for target, value in projects.items():
        project = _parse_project(target, value, _value_position(projects, target))
        if project is not None:
            yield project


def _group_projects(
    projects: Iterable[_CloudProject],
    apikeys: dict[str, str],
) -> list[_Group]:
    """Group projects by the API key that they are checked with.

    Projects naming an API key that no configuration file defines are left
    out, since there is no way to reach them.
    """
    groups: dict[str, _Group] = {}
    for project in projects:
        api_key = apikeys.get(project.apikey)
        if api_key is None:
            continue
        group = groups.setdefault(project.apikey, _Group(api_key))
        group.projects.append(project)
    return list(groups.values())


def _job_settings(client: Any, project: _CloudProject) -> list[str]:
    settings = dict(client.get_project(project.project_id).settings.list())
    job_settings = settings.get("job_settings")
    return list(job_settings) if isinstance(job_settings, dict) else []


def _setting_issues(
    checker: SettingChecker,
    project: _CloudProject,
    names: Iterable[str],
) -> Generator[Issue]:
    for name in names:
        for issue in checker.check_name_str(name, project.pos):
            issue.detail = f"{name} ({issue.detail})" if issue.detail else name
            yield issue


def _split_by_reachability(
    clients: list[Any],
    groups: list[_Group],
    executor: ThreadPoolExecutor,
) -> tuple[list[Issue], list[tuple[Any, _CloudProject]]]:
    """Return the issues for unreachable projects and the settings to read."""
    issues: list[Issue] = []
    targets: list[tuple[Any, _CloudProject]] = []
    reachable = executor.map(lambda c: set(c.projects.list()), clients)
    for client, group, ids in zip(clients, groups, reachable, strict=True):
        for project in group.projects:
            if project.project_id in ids:
                targets.append((client, project))
            else:
                detail = f"{project.target}: {project.project_id}"
                issues.append(Issue(UNREACHABLE_PROJECT, project.pos, detail))
    return issues, targets


def _check(groups: list[_Group], checker: SettingChecker) -> list[Issue]:
    from scrapinghub.client.exceptions import ScrapinghubAPIError  # noqa: PLC0415

    clients = [_client(group.api_key) for group in groups]
    try:
        with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as executor:
            issues, targets = _split_by_reachability(clients, groups, executor)
            names = executor.map(lambda t: _job_settings(*t), targets)
            for (_, project), setting_names in zip(targets, names, strict=True):
                issues.extend(_setting_issues(checker, project, setting_names))
    except (ScrapinghubAPIError, OSError) as e:
        raise CloudError(f"Scrapy Cloud API request failed: {e}") from None
    issues.sort(key=lambda issue: (issue.line, issue.column))
    return issues


def check() -> Generator[Issue]:
    """Yield the issues that checking Scrapy Cloud finds for the current project."""
    project = Project(Path.cwd())
    config_file = project.path / "scrapinghub.yml"
    if not config_file.exists():
        return
    try:
        data = YAML(typ="rt").load(config_file.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, YAMLError) as e:
        raise InputFileError(str(e), config_file) from None
    if not isinstance(data, CommentedMap):
        return
    _check_endpoints(data)
    apikeys = _api_keys(data)
    if not apikeys:
        raise CloudError(
            "no Scrapy Cloud API key found; set the SHUB_APIKEY environment variable "
            "or define apikeys.default in ~/.scrapinghub.yml",
        )
    groups = _group_projects(list(_iter_projects(data)), apikeys)
    if not groups:
        return
    context = Context(project)
    checker = SettingChecker(context)
    for issue in _check(groups, checker):
        if context.is_ignored(issue, config_file):
            continue
        issue.file = config_file.relative_to(project.path)
        yield issue
