from __future__ import annotations

import os
from collections.abc import Callable, Generator, Iterable, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Any, TypeAlias

import pytest
import tomli_w
from packaging.version import InvalidVersion, Version

from scrapy_lint._releases import _VENDORED_RELEASES, _parse, _read

if TYPE_CHECKING:
    from scrapy_lint.issues import Issue

NO_ISSUE = None
YEAR = timedelta(days=365)

SCRAPY_RELEASES = _parse(_read(_VENDORED_RELEASES / "scrapy.txt"))
SCRAPY_LATEST = max(SCRAPY_RELEASES)

pytest.register_assert_rewrite("tests.helpers")


@dataclass
class File:
    text: str | bytes
    path: str | None = None


@dataclass
class ExpectedIssue:
    message: str
    line: int = 1
    column: int = 0
    path: str | None = None

    @classmethod
    def from_issue(cls, issue: Issue) -> ExpectedIssue:
        assert issue.file
        return cls(
            message=issue.message,
            line=issue.pos.line,
            column=issue.pos.column,
            path=str(issue.file),
        )

    def replace(
        self,
        *,
        message: str | None = None,
        line: int | None = None,
        column: int | None = None,
        path: str | None = None,
    ) -> ExpectedIssue:
        return ExpectedIssue(
            message=message if message else self.message,
            line=line if line else self.line,
            column=column if column is not None else self.column,
            path=path if path else self.path,
        )


def outdated_scrapy_issue(
    version: Version | str | None,
    *,
    line: int = 1,
    path: str = "requirements.txt",
) -> ExpectedIssue:
    return ExpectedIssue(
        f"SCP47 outdated requirement: scrapy {version} predates "
        f"{SCRAPY_LATEST} by over a year",
        line=line,
        path=path,
    )


def outdated_scrapy(
    requirements: str | Sequence[str],
    *,
    path: str = "requirements.txt",
) -> tuple[ExpectedIssue, ...]:
    """Return the SCP47 issues expected for the scrapy pins in *requirements*.

    Tests about other rules use this instead of spelling SCP47 out, so that
    they keep passing as the vendored release data moves forward.
    """
    if not isinstance(requirements, str):
        requirements = "\n".join(requirements)
    issues = []
    for number, line in enumerate(requirements.splitlines(), start=1):
        name, _, version = line.partition("==")
        if name.strip() != "scrapy":
            continue
        try:
            released = SCRAPY_RELEASES.get(Version(version.strip()))
        except InvalidVersion:
            continue
        if released is None or SCRAPY_RELEASES[SCRAPY_LATEST] - released <= YEAR:
            continue
        issues.append(
            outdated_scrapy_issue(version.strip(), line=number, path=path),
        )
    return tuple(issues)


@contextmanager
def chdir(path: str | Path):
    old_cwd = Path.cwd()
    try:
        os.chdir(str(path))
        yield
    finally:
        os.chdir(str(old_cwd))


Files: TypeAlias = Sequence[File] | File
ExpectedIssues: TypeAlias = Sequence[ExpectedIssue] | ExpectedIssue | None
Options: TypeAlias = dict[str, Any]
Cases: TypeAlias = Sequence[tuple[Files, ExpectedIssues, Options]]


def cases(test_cases: Cases) -> Callable:
    def decorator(func):
        return pytest.mark.parametrize(
            ("files", "expected", "options"),
            test_cases,
            ids=range(len(test_cases)),
        )(func)

    return decorator


def iter_issues(
    issues: Iterable[ExpectedIssue] | ExpectedIssue | None,
) -> Generator[ExpectedIssue]:
    if issues is None:
        return
    if isinstance(issues, ExpectedIssue):
        yield issues
        return
    yield from issues


@contextmanager
def project(
    files: File | Sequence[File] | None = None,
    options: dict | None = None,
):
    if isinstance(files, File):
        files = [files]
    elif files is None:
        files = []
    with TemporaryDirectory() as directory:
        for file in files:
            assert file.path
            file_path = Path(directory) / file.path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(file.text, str):
                file_path.write_text(file.text)
            else:
                file_path.write_bytes(file.text)
        if options:
            options_path = Path(directory) / "pyproject.toml"
            toml_dict = {"tool": {"scrapy-lint": options}}
            with options_path.open("wb") as f:
                f.write(tomli_w.dumps(toml_dict).encode("utf-8"))
        with chdir(directory):
            yield directory
