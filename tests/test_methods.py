from __future__ import annotations

from inspect import cleandoc

from . import NO_ISSUE, Cases, ExpectedIssue, File, cases, iter_issues
from .helpers import check_project

DEPRECATION_VERSION = "2.14.0"
PARTIAL_FREEZE = ExpectedIssue(
    "SCP13 incomplete requirements freeze",
    path="requirements.txt",
)


def issue(line: int, column: int) -> ExpectedIssue:
    return ExpectedIssue(
        f"SCP51 deprecated argument: deprecated in scrapy "
        f"{DEPRECATION_VERSION}; keep the crawler from from_crawler() and use "
        f"its spider attribute instead",
        line=line,
        column=column,
        path="a.py",
    )


CASES: Cases = (
    *(
        (
            (
                File(f"scrapy=={version}", path="requirements.txt"),
                File(cleandoc(code), path="a.py"),
            ),
            (PARTIAL_FREEZE, *iter_issues(issues)),
            {},
        )
        for version, code, issues in (
            # Every affected method, and untouched neighbors.
            (
                DEPRECATION_VERSION,
                """
            class MyMiddleware:
                def process_request(self, request, spider):
                    pass

                def process_response(self, request, response, spider):
                    pass

                def process_exception(self, request, exception, spider):
                    pass

                def process_spider_input(self, response, spider):
                    pass

                async def process_spider_output(self, response, result, spider):
                    pass

                def process_spider_exception(self, response, exception, spider):
                    pass

                def process_item(self, item, spider):
                    pass

                def open_spider(self, spider):
                    pass

                def close_spider(self, spider):
                    pass

                async def fetch(self, request, spider):
                    pass

                def parse(self, response, spider):
                    pass
            """,
                (
                    issue(2, 39),
                    issue(5, 50),
                    issue(8, 52),
                    issue(11, 45),
                    issue(14, 60),
                    issue(17, 60),
                    issue(20, 33),
                    issue(23, 26),
                    issue(26, 27),
                    issue(29, 35),
                ),
            ),
            # Keyword-only and positional-only parameters.
            (
                DEPRECATION_VERSION,
                """
            class MyPipeline:
                name = "x"

                def process_item(self, item, /, *, spider):
                    pass

                def open_spider(self, spider=None):
                    pass

                def close_spider(self, *, spider=None):
                    pass
            """,
                issue(4, 39),
            ),
            # Older Scrapy versions.
            (
                "2.13.2",
                """
            class MyPipeline:
                def process_item(self, item, spider):
                    pass
            """,
                NO_ISSUE,
            ),
            # Functions outside a class body.
            (
                DEPRECATION_VERSION,
                """
            def process_item(item, spider):
                pass
            """,
                NO_ISSUE,
            ),
        )
    ),
    # No frozen Scrapy version.
    (
        (
            File(
                "class MyPipeline:\n    def process_item(self, item, spider):\n"
                "        pass",
                path="a.py",
            ),
        ),
        NO_ISSUE,
        {},
    ),
)


@cases(CASES)
def test(files, expected, options):
    check_project(files, expected, options)
