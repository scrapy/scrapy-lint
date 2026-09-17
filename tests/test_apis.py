from __future__ import annotations

from inspect import cleandoc

from packaging.version import Version

from . import (
    NO_ISSUE,
    SCRAPY_LATEST,
    Cases,
    ExpectedIssue,
    File,
    cases,
    insecure_scrapy_issues,
    iter_issues,
    outdated_scrapy,
)
from .helpers import check_project

PATH = "a.py"
REQUIREMENTS_PATH = "requirements.txt"
REMOVED_IN = Version("2.11.0")
BEFORE_REMOVAL = Version("2.10.0")
INCOMPLETE_FREEZE = ExpectedIssue(
    "SCP13 incomplete requirements freeze",
    path=REQUIREMENTS_PATH,
)
BINARY = "binary parameter of scrapy.exporters.PythonItemExporter"
DEPRECATED = (
    f"SCP74 deprecated API: {BINARY}, deprecated in scrapy 1.1.0; use binary=False"
)
REMOVED = (
    f"SCP75 removed API: {BINARY}, deprecated in scrapy 1.1.0, removed in {REMOVED_IN}"
)
DEPRECATED_IN = Version("2.17.0")
HELP = "help method of scrapy.commands.ScrapyCommand"
HELP_GUIDANCE = "Scrapy never calls it, use long_desc() instead"
COMMAND = cleandoc(
    """
    class Command(ScrapyCommand):
        def {method}(self):
            return "Long description"
    """,
)

CASES: Cases = (
    # Without a requirements file there is no version to check against.
    (
        File("PythonItemExporter(binary=True)", path=PATH),
        NO_ISSUE,
        {},
    ),
    *(
        (
            (
                File("", path="scrapy.cfg"),
                File(f"scrapy=={version}", path=REQUIREMENTS_PATH),
                File(code, path=PATH),
            ),
            (
                INCOMPLETE_FREEZE,
                *insecure_scrapy_issues(f"scrapy=={version}"),
                *outdated_scrapy(f"scrapy=={version}"),
                *iter_issues(issues),
            ),
            {},
        )
        for version, code, issues in (
            # SCP74: deprecated API
            *(
                (
                    BEFORE_REMOVAL,
                    code,
                    ExpectedIssue(DEPRECATED, column=column, path=PATH),
                )
                for code, column in (
                    ("PythonItemExporter(binary=True)", 19),
                    ("exporters.PythonItemExporter(binary=True)", 29),
                    ("scrapy.exporters.PythonItemExporter(binary=True)", 36),
                    ("PythonItemExporter(indent=2, binary=True)", 29),
                )
            ),
            # SCP74: deprecated API (no issue)
            *(
                (BEFORE_REMOVAL, code, NO_ISSUE)
                for code in (
                    # Only binary=True is deprecated before its removal.
                    "PythonItemExporter(binary=False)",
                    # Values that cannot be resolved statically are ignored.
                    "PythonItemExporter(binary=flag)",
                    "PythonItemExporter(**options)",
                    "PythonItemExporter(indent=2)",
                    "SomeOtherExporter(binary=True)",
                )
            ),
            # SCP75: removed API
            *(
                (
                    SCRAPY_LATEST,
                    code,
                    ExpectedIssue(REMOVED, column=column, path=PATH),
                )
                for code, column in (
                    ("PythonItemExporter(binary=False)", 19),
                    ("PythonItemExporter(binary=True)", 19),
                    ("PythonItemExporter(binary=flag)", 19),
                    ("exporters.PythonItemExporter(binary=False)", 29),
                )
            ),
            # SCP75: removed API (no issue)
            *(
                (SCRAPY_LATEST, code, NO_ISSUE)
                for code in (
                    "PythonItemExporter(**options)",
                    "PythonItemExporter(indent=2)",
                    "SomeOtherExporter(binary=False)",
                )
            ),
            # SCP77: discouraged API, on methods that are only deprecated in a
            # higher version.
            *(
                (
                    BEFORE_REMOVAL,
                    code,
                    ExpectedIssue(
                        f"SCP77 discouraged API: {subject}, to be deprecated in "
                        f"scrapy {DEPRECATED_IN}; {guidance}",
                        line=line,
                        column=column,
                        path=PATH,
                    ),
                )
                for code, subject, guidance, line, column in (
                    (COMMAND.format(method="help"), HELP, HELP_GUIDANCE, 2, 8),
                    (
                        COMMAND.format(method="help").replace(
                            "ScrapyCommand",
                            "commands.ScrapyCommand",
                        ),
                        HELP,
                        HELP_GUIDANCE,
                        2,
                        8,
                    ),
                )
            ),
            # SCP77: discouraged API (no issue)
            *(
                (BEFORE_REMOVAL, code, NO_ISSUE)
                for code in (
                    COMMAND.format(method="long_desc"),
                    COMMAND.format(method="help").replace("ScrapyCommand", "object"),
                )
            ),
            # From the deprecation version on, the same uses become SCP74.
            *(
                (
                    DEPRECATED_IN,
                    code,
                    ExpectedIssue(
                        f"SCP74 deprecated API: {subject}, deprecated in "
                        f"scrapy {DEPRECATED_IN}; {guidance}",
                        line=line,
                        column=column,
                        path=PATH,
                    ),
                )
                for code, subject, guidance, line, column in (
                    (COMMAND.format(method="help"), HELP, HELP_GUIDANCE, 2, 8),
                )
            ),
        )
    ),
)


@cases(CASES)
def test(
    files: File | list[File],
    expected: ExpectedIssue | list[ExpectedIssue] | None,
    options,
):
    check_project(files, expected, options)
