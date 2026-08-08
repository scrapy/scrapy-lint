from __future__ import annotations

from inspect import cleandoc

from . import NO_ISSUE, Cases, ExpectedIssue, File, cases
from .helpers import check_project

CASES: Cases = (
    (
        File(
            cleandoc(
                """
                class MySpider(Spider):
                    name = "myspider"
                    start_url = "https://toscrape.com"
                """,
            ),
            path="a.py",
        ),
        ExpectedIssue(
            message="SCP47 start_url instead of start_urls",
            line=3,
            column=4,
            path="a.py",
        ),
        {},
    ),
    # A class that also defines start_urls is left alone.
    (
        File(
            cleandoc(
                """
                class MySpider(Spider):
                    start_url = "https://a.example"
                    start_urls = ["https://b.example"]
                """,
            ),
            path="a.py",
        ),
        NO_ISSUE,
        {},
    ),
    # start_url outside a class body is not a spider attribute.
    (
        File('start_url = "https://toscrape.com"\n', path="a.py"),
        NO_ISSUE,
        {},
    ),
)


@cases(CASES)
def test(
    files: File | list[File],
    expected: ExpectedIssue | list[ExpectedIssue] | None,
    options: dict,
):
    check_project(files, expected, options)
