from __future__ import annotations

import os
from collections.abc import Callable, Generator, Iterable, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Any, TypeAlias

import pytest
import tomli_w
from packaging.version import Version

from scrapy_lint.data.packages import PACKAGES

if TYPE_CHECKING:
    from scrapy_lint.issues import Issue

NO_ISSUE = None

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


def insecure_scrapy_issues(
    requirements: Iterable[str] | str,
) -> Generator[ExpectedIssue]:
    """SCP15 issues for the frozen, insecure Scrapy pins in *requirements*.

    Fixtures that pin Scrapy get these on top of whatever they are testing, so
    deriving them keeps the lowest safe version out of the expected messages.
    """
    lowest_safe = PACKAGES["scrapy"].lowest_safe_version
    assert lowest_safe
    if isinstance(requirements, str):
        requirements = requirements.splitlines()
    for line, requirement in enumerate(requirements, start=1):
        name, separator, version = requirement.partition("==")
        if name != "scrapy" or not separator or Version(version) >= lowest_safe:
            continue
        yield ExpectedIssue(
            f"SCP15 insecure requirement: scrapy {lowest_safe} implements "
            f"security fixes",
            line=line,
            path="requirements.txt",
        )


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
