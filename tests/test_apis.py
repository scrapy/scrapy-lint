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
INCOMPLETE_FREEZE = ExpectedIssue(
    "SCP13 incomplete requirements freeze",
    path=REQUIREMENTS_PATH,
)
INSECURE = ExpectedIssue(
    "SCP15 insecure requirement: scrapy 2.11.2 implements security fixes",
    path=REQUIREMENTS_PATH,
)
BINARY = "binary parameter of scrapy.exporters.PythonItemExporter"
DEPRECATED = (
    f"SCP47 deprecated API: {BINARY}, deprecated in scrapy 1.1.0; use binary=False"
)
REMOVED = (
    f"SCP48 removed API: {BINARY}, deprecated in scrapy 1.1.0, removed in {REMOVED_IN}"
)
DEPRECATED_IN = Version("2.17.0")
HELP = "help method of scrapy.commands.ScrapyCommand"
HELP_GUIDANCE = "Scrapy never calls it, use long_desc() instead"
TLS = "scrapy.core.downloader.tls.METHOD_TLS"
SSL = "scrapy.utils.ssl.get_temp_key_info"
INTERNAL = "intended for internal use only"
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
            # SCP47: deprecated API
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
            # SCP47: deprecated API (no issue)
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
            # SCP48: removed API
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
            # SCP48: removed API (no issue)
            *(
                (LATEST, code, NO_ISSUE)
                for code in (
                    "PythonItemExporter(**options)",
                    "PythonItemExporter(indent=2)",
                    "SomeOtherExporter(binary=False)",
                )
            ),
            # SCP50: discouraged API, on methods and module members that are
            # only deprecated in a higher version.
            *(
                (
                    LATEST,
                    code,
                    ExpectedIssue(
                        f"SCP50 discouraged API: {subject}, to be deprecated in "
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
                    (
                        "from scrapy.core.downloader.tls import METHOD_TLS",
                        TLS,
                        INTERNAL,
                        1,
                        39,
                    ),
                    (
                        "from scrapy.utils.ssl import get_temp_key_info as info",
                        SSL,
                        INTERNAL,
                        1,
                        50,
                    ),
                )
            ),
            # SCP50: discouraged API (no issue)
            *(
                (LATEST, code, NO_ISSUE)
                for code in (
                    COMMAND.format(method="long_desc"),
                    COMMAND.format(method="help").replace("ScrapyCommand", "object"),
                    "from scrapy.core.downloader import tls",
                    "from scrapy.core.downloader.tls import ScrapyClientTLSOptions",
                    "from . import METHOD_TLS",
                    "import scrapy.utils.ssl",
                )
            ),
            # From the deprecation version on, the same uses become SCP47.
            *(
                (
                    DEPRECATED_IN,
                    code,
                    ExpectedIssue(
                        f"SCP47 deprecated API: {subject}, deprecated in "
                        f"scrapy {DEPRECATED_IN}; {guidance}",
                        line=line,
                        column=column,
                        path=PATH,
                    ),
                )
                for code, subject, guidance, line, column in (
                    (COMMAND.format(method="help"), HELP, HELP_GUIDANCE, 2, 8),
                    (
                        "from scrapy.core.downloader.tls import METHOD_TLS",
                        TLS,
                        INTERNAL,
                        1,
                        39,
                    ),
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
