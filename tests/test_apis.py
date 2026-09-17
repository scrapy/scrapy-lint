from __future__ import annotations

from inspect import cleandoc

from packaging.version import Version

from scrapy_lint.data.packages import PACKAGES

from . import (
    NO_ISSUE,
    Cases,
    ExpectedIssue,
    File,
    cases,
    insecure_scrapy_issues,
    iter_issues,
)
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
BINARY = "binary parameter of scrapy.exporters.PythonItemExporter"
DEPRECATED = (
    f"SCP74 deprecated API: {BINARY}, deprecated in scrapy 1.1.0; use binary=False"
)
REMOVED = (
    f"SCP75 removed API: {BINARY}, deprecated in scrapy 1.1.0, removed in "
    f"{REMOVED_IN}; remove it, the output is no longer binary"
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
BEFORE_START_REMOVAL = Version("2.15.0")
SPIDER = "scrapy.Spider"
SPIDER_MW = "scrapy.spidermiddlewares.SpiderMiddleware"
START = "define start() instead"
PROCESS_START = "define process_start() instead"
ASYNC_OUTPUT = "define it as an asynchronous generator instead"


def component(*declarations: str, base: str = "") -> str:
    """Return a class with the given method *declarations*, extending *base*
    where given."""
    header = f"class MyComponent({base}):" if base else "class MyComponent:"
    body = "".join(f"    {d}(self, *args):\n        pass\n" for d in declarations)
    return f"{header}\n{body}"


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
            # SCP74: deprecated method overrides.
            *(
                (
                    version,
                    component(f"def {method}", base=base),
                    ExpectedIssue(
                        f"SCP74 deprecated API: {method} method of {path}, "
                        f"deprecated in scrapy {deprecated_in}; {guidance}",
                        line=2,
                        column=8,
                        path=PATH,
                    ),
                )
                for version, base, method, path, deprecated_in, guidance in (
                    (
                        BEFORE_START_REMOVAL,
                        "Spider",
                        "start_requests",
                        SPIDER,
                        "2.13.0",
                        START,
                    ),
                    (
                        BEFORE_START_REMOVAL,
                        "BaseSpiderMiddleware",
                        "process_spider_output",
                        SPIDER_MW,
                        "2.13.0",
                        ASYNC_OUTPUT,
                    ),
                    (
                        LATEST,
                        "Contract",
                        "add_pre_hook",
                        "scrapy.contracts.Contract",
                        "2.19.0",
                        "define pre_process() instead",
                    ),
                    (
                        LATEST,
                        "Contract",
                        "add_post_hook",
                        "scrapy.contracts.Contract",
                        "2.19.0",
                        "define post_process() instead",
                    ),
                    (
                        LATEST,
                        "RFPDupeFilter",
                        "request_fingerprint",
                        "scrapy.dupefilters.RFPDupeFilter",
                        "2.19.0",
                        "set the REQUEST_FINGERPRINTER_CLASS setting instead",
                    ),
                )
            ),
            # A method deprecated in a higher version, with no reason to stop
            # using it yet, is not reported.
            (
                BEFORE_START_REMOVAL,
                component("def add_pre_hook", base="Contract"),
                NO_ISSUE,
            ),
            # SCP75: removed methods, reported on subclasses of the class that
            # defines them, and, for the methods of an interface, on classes
            # with no base class at all.
            *(
                (
                    LATEST,
                    component(f"def {method}", base=base),
                    ExpectedIssue(
                        f"SCP75 removed API: {method} method of {path}, deprecated "
                        f"in scrapy 2.13.0, removed in 2.16.0; {guidance}",
                        line=2,
                        column=8,
                        path=PATH,
                    ),
                )
                for base, method, path, guidance in (
                    ("Spider", "start_requests", SPIDER, START),
                    ("CrawlSpider", "start_requests", SPIDER, START),
                    ("ProjectSpider", "start_requests", SPIDER, START),
                    ("", "process_start_requests", SPIDER_MW, PROCESS_START),
                    (
                        "BaseSpiderMiddleware",
                        "process_start_requests",
                        SPIDER_MW,
                        PROCESS_START,
                    ),
                    ("", "process_spider_output", SPIDER_MW, ASYNC_OUTPUT),
                    (
                        "BaseSpiderMiddleware",
                        "process_spider_output",
                        SPIDER_MW,
                        ASYNC_OUTPUT,
                    ),
                )
            ),
            # Methods (no issue)
            *(
                (version, code, NO_ISSUE)
                for version in (BEFORE_START_REMOVAL, LATEST)
                for code in (
                    component("def start_requests", base="object"),
                    component("def parse", base="Spider"),
                    # The asynchronous generator that replaces the deprecated
                    # process_spider_output() keeps its name.
                    component("async def process_spider_output"),
                    # A universal spider middleware defines both.
                    component(
                        "def process_spider_output",
                        "async def process_spider_output_async",
                    ),
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
