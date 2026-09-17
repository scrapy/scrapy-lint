from __future__ import annotations

from inspect import cleandoc

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

DEPRECATION_VERSION = "2.14.0"
PARTIAL_FREEZE = ExpectedIssue(
    "SCP13 incomplete requirements freeze",
    path="requirements.txt",
)


def issue(line: int, column: int, setting: str) -> ExpectedIssue:
    return ExpectedIssue(
        f"SCP48 deprecated spider attribute: deprecated in scrapy "
        f"{DEPRECATION_VERSION}; use the {setting} setting instead",
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
            (
                PARTIAL_FREEZE,
                *insecure_scrapy_issues(f"scrapy=={version}"),
                *iter_issues(issues),
            ),
            {},
        )
        for version, code, issues in (
            # Every deprecated attribute, and untouched neighbors.
            (
                DEPRECATION_VERSION,
                """
            class ToScrapeComSpider(Spider):
                name = "toscrape_com"
                download_maxsize = 1
                download_timeout = 1
                download_warnsize = 1
                max_concurrent_requests = 1
                user_agent = "Example"
                custom_settings = {"DOWNLOAD_TIMEOUT": 1}
            """,
                (
                    issue(3, 4, "DOWNLOAD_MAXSIZE"),
                    issue(4, 4, "DOWNLOAD_TIMEOUT"),
                    issue(5, 4, "DOWNLOAD_WARNSIZE"),
                    issue(6, 4, "CONCURRENT_REQUESTS_PER_DOMAIN"),
                    issue(7, 4, "USER_AGENT"),
                ),
            ),
            # Annotated and chained assignments, attribute base classes.
            (
                DEPRECATION_VERSION,
                """
            class ToScrapeComSpider(scrapy.spiders.CrawlSpider):
                download_timeout: float = 1
                download_maxsize = download_warnsize = 1
            """,
                (
                    issue(2, 4, "DOWNLOAD_TIMEOUT"),
                    issue(3, 4, "DOWNLOAD_MAXSIZE"),
                    issue(3, 23, "DOWNLOAD_WARNSIZE"),
                ),
            ),
            # Older Scrapy versions.
            (
                "2.13.2",
                """
            class ToScrapeComSpider(Spider):
                download_timeout = 1
            """,
                NO_ISSUE,
            ),
            # Classes that do not look like spiders.
            (
                DEPRECATION_VERSION,
                """
            class Downloader:
                download_timeout = 1
            """,
                NO_ISSUE,
            ),
            # Assignments outside a spider class body.
            (
                DEPRECATION_VERSION,
                """
            download_timeout = 1


            class ToScrapeComSpider(Spider):
                def parse(self, response):
                    download_timeout = 1
            """,
                NO_ISSUE,
            ),
        )
    ),
    # An attribute deprecated in a later version, with its own guidance.
    (
        (
            File("scrapy==2.18.0", path="requirements.txt"),
            File(
                "class ToScrapeComSpider(Spider):\n    download_delay = 1",
                path="a.py",
            ),
        ),
        (
            PARTIAL_FREEZE,
            ExpectedIssue(
                "SCP48 deprecated spider attribute: deprecated in scrapy 2.18.0; "
                "use the DOWNLOAD_DELAY setting, or DOWNLOAD_SLOTS for per-domain "
                "delays, instead",
                line=2,
                column=4,
                path="a.py",
            ),
        ),
        {},
    ),
    # No frozen Scrapy version.
    (
        (
            File(
                "class ToScrapeComSpider(Spider):\n    download_timeout = 1",
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
