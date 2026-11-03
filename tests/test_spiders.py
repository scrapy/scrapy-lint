from __future__ import annotations

from inspect import cleandoc
from textwrap import dedent, indent

from . import NO_ISSUE, Cases, ExpectedIssue, File, cases
from .helpers import check_project

PATH = "a.py"
HEADER = """\
from scrapy import Request, Spider


class MySpider(Spider):
    name = "my"

"""


def spider(body: str) -> str:
    return HEADER + indent(dedent(body), "    ")


ISSUE = ExpectedIssue(
    message="SCP54 unneeded start method",
    line=7,
    column=4,
    path=PATH,
)
CASES: Cases = tuple(
    (File(spider(code), path=PATH), issues, {})
    for code, issues in (
        *(
            (code, ISSUE)
            for code in (
                """\
                    async def start(self):
                        yield Request("https://toscrape.com/")
                """,
                """\
                    async def start(self):
                        yield Request("https://a.example/")
                        yield Request("https://b.example/")
                """,
                """\
                    async def start(self):
                        yield Request(url="https://toscrape.com/", dont_filter=True)
                """,
                """\
                    async def start(self):
                        yield Request("https://toscrape.com/", callback=self.parse)
                """,
                """\
                    async def start(self):
                        for url in self.start_urls:
                            yield Request(url, dont_filter=True)
                """,
                """\
                    async def start(self):
                        for url in ["https://toscrape.com/"]:
                            yield Request(url)
                """,
                """\
                    def start_requests(self):
                        yield Request("https://toscrape.com/")
                """,
                """\
                    async def start(self):
                        \"\"\"Docstrings do not make the method needed.\"\"\"
                        yield Request("https://toscrape.com/")
                """,
            )
        ),
        *(
            (code, NO_ISSUE)
            for code in (
                # Parameters that start_urls cannot cover.
                """\
                    async def start(self):
                        yield Request("https://toscrape.com/", meta={"a": "b"})
                """,
                """\
                    async def start(self):
                        yield Request("https://toscrape.com/", callback=self.parse_home)
                """,
                """\
                    async def start(self):
                        yield Request("https://toscrape.com/", **self.kwargs)
                """,
                # Request subclasses are not what start_urls sends.
                """\
                    async def start(self):
                        yield JsonRequest("https://toscrape.com/")
                """,
                # Anything beyond plain, unconditional requests.
                """\
                    async def start(self):
                        yield Request()
                """,
                """\
                    async def start(self):
                        yield Request(self.url)
                """,
                """\
                    async def start(self):
                        yield Request("https://toscrape.com/", dont_filter=self.filter)
                """,
                """\
                    async def start(self):
                        yield {"foo": "bar"}
                """,
                """\
                    async def start(self):
                        yield from super().start()
                """,
                """\
                    async def start(self):
                        for url in await self.get_urls():
                            yield Request(url)
                """,
                """\
                    async def start(self):
                        for url in self.start_urls:
                            if url:
                                yield Request(url)
                """,
                """\
                    async def start(self):
                        for url in self.start_urls:
                            yield Request(f"{url}?a=b")
                """,
                """\
                    async def start(self):
                        for url in self.start_urls:
                            yield Request(url)
                        else:
                            pass
                """,
                """\
                    async def start(self):
                        for url in self.start_urls:
                            yield Request(url)
                            yield Request(url)
                """,
                """\
                    async def start(self):
                        for url, method in self.start_targets:
                            yield Request(url)
                """,
                """\
                    async def start(self):
                        if self.mode:
                            yield Request("https://toscrape.com/")
                """,
                """\
                    async def start(self):
                        \"\"\"Nothing to yield.\"\"\"
                """,
                # Methods that are not spider start methods.
                """\
                    def parse(self, response):
                        yield Request("https://toscrape.com/")
                """,
            )
        ),
    )
)
BASE_CASES: Cases = (
    # A base class that is not a Scrapy spider class may define a start method
    # that the spider would inherit without its own.
    (
        File(
            cleandoc(
                """
                class MySpider(MyBaseSpider):
                    start_urls = ["https://toscrape.com/"]

                    async def start(self):
                        for url in self.start_urls:
                            yield Request(url, dont_filter=True)
                """,
            ),
            path=PATH,
        ),
        NO_ISSUE,
        {},
    ),
    # So may a mixin.
    (
        File(
            cleandoc(
                """
                class MySpider(MyMixin, Spider):
                    async def start(self):
                        yield Request("https://toscrape.com/")
                """,
            ),
            path=PATH,
        ),
        NO_ISSUE,
        {},
    ),
    # A class without bases is not a spider.
    (
        File(
            cleandoc(
                """
                class MySpider:
                    async def start(self):
                        yield Request("https://toscrape.com/")
                """,
            ),
            path=PATH,
        ),
        NO_ISSUE,
        {},
    ),
    # Scrapy spider classes are still reported, however they are referenced.
    *(
        (
            File(
                cleandoc(
                    f"""
                    class MySpider({base}):
                        async def start(self):
                            yield Request("https://toscrape.com/")
                    """,
                ),
                path=PATH,
            ),
            ExpectedIssue(
                message="SCP54 unneeded start method",
                line=2,
                column=4,
                path=PATH,
            ),
            {},
        )
        for base in ("scrapy.Spider", "CrawlSpider")
    ),
)


@cases((*CASES, *BASE_CASES))
def test_main(files, expected, options):
    check_project(files, expected, options)
