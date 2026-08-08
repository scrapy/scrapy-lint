from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from shutil import which
from subprocess import DEVNULL, PIPE, SubprocessError, run
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING
from urllib.request import urlopen

from platformdirs import user_cache_dir

from scrapy_lint.requirements import iter_requirement_lines, pinned_version

if TYPE_CHECKING:
    from packaging.version import Version

_FROZEN_SCRAPY_STACK = re.compile(r"scrapy:(?P<tag>[\w.-]*-\d{8})")
_PYTHON_VERSION = re.compile(r"pip-compile with Python (?P<version>\d+\.\d+)")
_REQUIREMENTS_URL = (
    "https://raw.githubusercontent.com/scrapinghub/scrapinghub-stack-scrapy"
    "/{tag}/requirements.txt"
)
_DOWNLOAD_TIMEOUT = 5
_RESOLUTION_TIMEOUT = 60
_VENDORED_STACKS = Path(__file__).parent / "data" / "stacks"


@dataclass
class Stack:
    requirements: dict[str, Version]
    python_version: str | None


def stack_data(value: str) -> Stack | None:
    """Return the contents of the *value* Scrapy Cloud stack.

    The result is ``None`` for stacks that are not supported, and for stacks
    whose contents cannot be determined, e.g. while offline.
    """
    match = _FROZEN_SCRAPY_STACK.fullmatch(value)
    if not match:
        return None
    text = _requirements_text(match["tag"])
    if text is None:
        return None
    python_version = _PYTHON_VERSION.search(text)
    return Stack(
        requirements={
            name: version
            for _, name, requirement in iter_requirement_lines(text.splitlines())
            if (version := pinned_version(requirement)) is not None
        },
        python_version=python_version["version"] if python_version else None,
    )


def find_conflict(stack: Stack, requirements: dict[str, Version]) -> str | None:
    """Return why *requirements* cannot be installed on top of *stack*.

    The deployed environment is the stack with *requirements* installed on top,
    i.e. the versions in *requirements* replace those of the stack, while the
    rest of the stack stays as it is. The result is ``None`` when that
    environment is sound, and when it cannot be verified, e.g. without uv.
    """
    uv = which("uv")
    if uv is None:
        return None
    with TemporaryDirectory() as directory:
        path = Path(directory)
        # Only report a conflict that the stack does not have on its own, so
        # that a resolver that cannot do its job, e.g. for lack of network
        # access to package metadata, reports nothing.
        if _resolution_error(uv, stack, stack.requirements, path) is not None:
            return None
        installed = {**stack.requirements, **requirements}
        return _resolution_error(uv, stack, installed, path) or None


def _resolution_error(
    uv: str,
    stack: Stack,
    requirements: dict[str, Version],
    directory: Path,
) -> str | None:
    """Return why *requirements* do not resolve, empty if uv cannot run."""
    input_path = directory / "requirements.in"
    input_path.write_text(
        "".join(f"{name}=={version}\n" for name, version in requirements.items()),
        encoding="utf-8",
    )
    command = [
        uv,
        "pip",
        "compile",
        "--quiet",
        "--no-header",
        "--output-file",
        str(directory / "requirements.txt"),
    ]
    if stack.python_version:
        command += ["--python-version", stack.python_version]
    command.append(str(input_path))
    try:
        process = run(  # noqa: S603
            command,
            stdout=DEVNULL,
            stderr=PIPE,
            text=True,
            check=False,
            timeout=_RESOLUTION_TIMEOUT,
        )
    except (OSError, SubprocessError):
        return ""
    if process.returncode == 0:
        return None
    # Drop the box-drawing decorations that uv puts in front of every line.
    lines = (re.sub(r"^\W+", "", line) for line in process.stderr.splitlines())
    return " ".join(" ".join(lines).split())


def _requirements_text(tag: str) -> str | None:
    cache_path = _cache_path(tag)
    text = _read(_VENDORED_STACKS / f"{tag}.txt") or _read(cache_path)
    if text:
        return text
    try:
        text = _download(_REQUIREMENTS_URL.format(tag=tag))
    except (OSError, UnicodeDecodeError):
        return None
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(text, encoding="utf-8")
    except OSError:
        pass
    return text


def _cache_path(tag: str) -> Path:
    return Path(user_cache_dir("scrapy-lint")) / "stacks" / f"{tag}.txt"


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def _download(url: str) -> str:
    with urlopen(url, timeout=_DOWNLOAD_TIMEOUT) as response:  # noqa: S310
        return response.read().decode("utf-8")
