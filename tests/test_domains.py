from __future__ import annotations

from . import Cases, ExpectedIssue, File, cases
from .helpers import check_project

CASES: Cases = (
    # Assignments other than allowed_domains and start_urls must not cause
    # issues.
    (
        (
            File(
                """
                class MySpider(Spider):
                    allowed_domains = (
                        "a.example",
                        "b.example",
                        "https://toscrape.com",
                    )
                    start_urls = [
                        "https://c.example",
                        "https://d.example",
                    ]
                    foo = 'bar'
                """,
                path="a.py",
            ),
        ),
        (
            ExpectedIssue(
                message="SCP01 disallowed domain",
                line=8,
                column=8,
                path="a.py",
            ),
            ExpectedIssue(
                message="SCP01 disallowed domain",
                line=9,
                column=8,
                path="a.py",
            ),
            ExpectedIssue(
                message="SCP02 URL in allowed_domains",
                line=5,
                column=8,
                path="a.py",
            ),
        ),
        {},
    ),
    (
        (
            File(
                cleandoc(
                    """
                    class MySpider(Spider):
                        allowed_domains = ['toscrape.com:8080', '127.0.0.1:8080']
                    """
                ),
                path="a.py",
            ),
        ),
        (
            ExpectedIssue(
                message="SCP02 port in allowed_domains",
                line=2,
                column=23,
                path="a.py",
            ),
            ExpectedIssue(
                message="SCP02 port in allowed_domains",
                line=2,
                column=44,
                path="a.py",
            ),
        ),
        {},
    ),
    # The allowed_domains from a given class should not affect other classes.
    (
        (
            File(
                """
                class ASpider(Spider):
                    name = 'a'
                    start_urls = ['https://a.example/']

                class BSpider(Spider):
                    name = 'b'
                    allowed_domains = ['b.example']
                    start_urls = ['https://b.example/']
                """,
                path="a.py",
            ),
        ),
        ExpectedIssue(
            message="SCP57 no allowed_domains",
            line=1,
            column=6,
            path="a.py",
        ),
        {},
    ),
    # SCP57
    (
        (
            File(
                """
                class AnnotatedSpider(scrapy.spiders.CrawlSpider):
                    allowed_domains: list[str] = ['a.example']
                    start_urls: list[str] = ['https://a.example/']

                class NotASpider:
                    start_urls = ['https://a.example/']

                class CustomSpider(MyBaseSpider):
                    start_urls = ['https://a.example/']

                class LateSpider(scrapy.Spider):
                    start_urls = ['https://a.example/']

                    def __init__(self, *args, **kwargs):
                        super().__init__(*args, **kwargs)
                        self.allowed_domains = ['a.example']
                """,
                path="a.py",
            ),
        ),
        ExpectedIssue(
            message="SCP57 no allowed_domains",
            line=11,
            column=6,
            path="a.py",
        ),
        {},
    ),
)


@cases(CASES)
def test(
    files: File | list[File],
    expected: ExpectedIssue | list[ExpectedIssue] | None,
    options,
):
    check_project(files, expected, options)
