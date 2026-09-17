from __future__ import annotations

from inspect import cleandoc

from packaging.version import Version

from scrapy_lint.data.packages import PACKAGES

from . import NO_ISSUE, Cases, ExpectedIssue, File, cases, iter_issues
from .helpers import check_project

PATH = "a.py"
REQUIREMENTS_PATH = "requirements.txt"
REMOVED_IN = Version("2.11.0")
BEFORE_REMOVAL = Version("2.10.0")
LATEST = PACKAGES["scrapy"].highest_known_version
LOWEST_SAFE = PACKAGES["scrapy"].lowest_safe_version
INCOMPLETE_FREEZE = ExpectedIssue(
    "SCP13 incomplete requirements freeze",
    path=REQUIREMENTS_PATH,
)
INSECURE = ExpectedIssue(
    f"SCP15 insecure requirement: scrapy {LOWEST_SAFE} implements security fixes",
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
FROM_RESPONSE = "from_response method of scrapy.FormRequest"
FROM_RESPONSE_DEPRECATED_IN = Version("2.16.0")
FROM_RESPONSE_GUIDANCE = "use form2request instead"
FROM_RESPONSE_DEPRECATED = (
    f"SCP74 deprecated API: {FROM_RESPONSE}, deprecated in scrapy "
    f"{FROM_RESPONSE_DEPRECATED_IN}; {FROM_RESPONSE_GUIDANCE}"
)
FROM_RESPONSE_DISCOURAGED = (
    f"SCP77 discouraged API: {FROM_RESPONSE}, to be deprecated in scrapy "
    f"{FROM_RESPONSE_DEPRECATED_IN}; {FROM_RESPONSE_GUIDANCE}"
)
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
                *([INSECURE] if version == BEFORE_REMOVAL else []),
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
                    LATEST,
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
                (LATEST, code, NO_ISSUE)
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
            # Methods called on their class.
            *(
                (
                    version,
                    code,
                    ExpectedIssue(message, column=column, path=PATH),
                )
                for version, message in (
                    (LATEST, FROM_RESPONSE_DEPRECATED),
                    (BEFORE_REMOVAL, FROM_RESPONSE_DISCOURAGED),
                )
                for code, column in (
                    ("FormRequest.from_response(response)", 0),
                    ("http.FormRequest.from_response(response)", 0),
                    ("scrapy.FormRequest.from_response(response)", 0),
                    ("scrapy.http.FormRequest.from_response(response)", 0),
                    ("request = FormRequest.from_response(response)", 10),
                )
            ),
            # Methods called on their class (no issue).
            *(
                (LATEST, code, NO_ISSUE)
                for code in (
                    "Foo.from_response(response)",
                    "from_response(response)",
                    "FormRequest(url)",
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
