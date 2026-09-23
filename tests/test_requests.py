from __future__ import annotations

from . import NO_ISSUE, Cases, ExpectedIssue, File, cases
from .helpers import check_project

PATH = "a.py"
CASES: Cases = (
    *(
        (
            File(code, path=PATH),
            issues,
            {},
        )
        for code, issues in (
            # Baseline
            *(
                (code, NO_ISSUE)
                for code in (
                    'Request(url, meta={"foo": "bar"})',
                    "Request(url, meta=meta)",
                )
            ),
            # SCP45 unsafe meta copy
            *(
                (
                    code,
                    ExpectedIssue(
                        message="SCP45 unsafe meta copy",
                        column=column,
                        path=PATH,
                    ),
                )
                for code, column in (
                    ('Request(url, self.parse, "GET", response.meta)', 32),
                    ("scrapy.FormRequest(url, meta=response.meta)", 29),
                    ("response.follow_all(urls, meta=response.meta)", 31),
                )
            ),
            # SCP46 raw Zyte API params
            *(
                (code, NO_ISSUE)
                for code in ('Request(url, meta={"zyte_api_automap": True})',)
            ),
            *(
                (
                    code,
                    ExpectedIssue(
                        message="SCP46 raw Zyte API params",
                        column=column,
                        path=PATH,
                    ),
                )
                for code, column in (
                    ('Request(url, meta={"zyte_api": {"httpResponseBody": True}})', 19),
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


UNUSED_AUTOMAP_PARAMS = "SCP83 unused automap params"
MISSING_PROVIDER_PARAMS = "SCP84 missing provider params"
AUTOMAP = 'meta={"zyte_api_automap": {"geolocation": "ie"}}'


def automap_issue(message: str, source: str) -> ExpectedIssue:
    """Point at the ``zyte_api_automap`` key of *source*."""
    for line, text in enumerate(source.splitlines(), 1):
        column = text.find('"zyte_api_automap"')
        if column >= 0:
            return ExpectedIssue(
                message=message,
                line=line,
                column=column,
                path=PATH,
            )
    raise ValueError(source)


CALLBACK_CASES: Cases = tuple(
    (
        File(source, path=PATH),
        automap_issue(message, source) if message else NO_ISSUE,
        {},
    )
    for source, message in (
        # SCP83: the callback discards the response, so scrapy-poet skips the
        # download and the params never reach Zyte API.
        (
            f"""\
from scrapy import Request, Spider
from scrapy_poet import DummyResponse


class MySpider(Spider):
    async def start(self):
        yield Request(url, self.parse_page, {AUTOMAP})

    def parse_page(self, response: DummyResponse):
        pass
""",
            UNUSED_AUTOMAP_PARAMS,
        ),
        (
            f"""\
from scrapy import Request, Spider
from scrapy_poet import DummyResponse


class MySpider(Spider):
    async def start(self):
        yield Request(url, callback=self.parse_page, {AUTOMAP})

    async def parse_page(self, response: DummyResponse, product: Product):
        pass
""",
            UNUSED_AUTOMAP_PARAMS,
        ),
        # No callback means the parse method.
        (
            f"""\
from scrapy import Request, Spider
from scrapy_poet import DummyResponse


class MySpider(Spider):
    async def start(self):
        yield Request(url, {AUTOMAP})

    def parse(self, response: DummyResponse):
        pass
""",
            UNUSED_AUTOMAP_PARAMS,
        ),
        (
            f"""\
import scrapy_poet
from scrapy import Spider


class MySpider(Spider):
    def parse(self, response: scrapy_poet.DummyResponse):
        yield response.follow(url, {AUTOMAP})
""",
            UNUSED_AUTOMAP_PARAMS,
        ),
        (
            f"""\
from scrapy import Request
from scrapy_poet import DummyResponse


def parse_page(response: DummyResponse):
    pass


Request(url, callback=parse_page, {AUTOMAP})
""",
            UNUSED_AUTOMAP_PARAMS,
        ),
        # SCP84: the response is used, but the page objects are fetched through
        # the provider, which ignores automap params.
        (
            f"""\
from scrapy import Request, Spider
from zyte_common_items import Product


class MySpider(Spider):
    async def start(self):
        yield Request(url, self.parse_page, {AUTOMAP})

    def parse_page(self, response, product: Product):
        pass
""",
            MISSING_PROVIDER_PARAMS,
        ),
        (
            f"""\
import web_poet
from scrapy import Request, Spider


class MySpider(Spider):
    async def start(self):
        yield Request(url, self.parse_page, {AUTOMAP})

    def parse_page(self, response, page: web_poet.WebPage):
        pass
""",
            MISSING_PROVIDER_PARAMS,
        ),
        (
            f"""\
import web_poet as wp
from scrapy import Request, Spider


class MySpider(Spider):
    async def start(self):
        yield Request(url, self.parse_page, {AUTOMAP})

    def parse_page(self, response, *, page: wp.WebPage):
        pass
""",
            MISSING_PROVIDER_PARAMS,
        ),
        (
            f"""\
from scrapy import Request, Spider
from typing import Annotated
from zyte_common_items import Product as Item


class MySpider(Spider):
    async def start(self):
        yield Request(url, self.parse_page, {AUTOMAP})

    def parse_page(self, response, product: Annotated[Item, "..."]):
        pass
""",
            MISSING_PROVIDER_PARAMS,
        ),
        # Provider params already set for the request.
        (
            """\
from scrapy import Request, Spider
from zyte_common_items import Product


class MySpider(Spider):
    async def start(self):
        yield Request(
            url,
            self.parse_page,
            meta={
                "zyte_api_automap": {"geolocation": "ie"},
                "zyte_api_provider": {"geolocation": "ie"},
            },
        )

    def parse_page(self, response, product: Product):
        pass
""",
            None,
        ),
        # Annotations that do not come from a page object package.
        (
            f"""\
from scrapy import Request, Spider

from .items import Product


class MySpider(Spider):
    async def start(self):
        yield Request(url, self.parse_page, {AUTOMAP})

    def parse_page(self, response, product: Product):
        pass
""",
            None,
        ),
        (
            f"""\
from scrapy import Request, Spider


class MySpider(Spider):
    async def start(self):
        yield Request(url, self.parse_page, {AUTOMAP})

    def parse_page(self, response, product: dict, page: "WebPage"):
        pass
""",
            None,
        ),
        # Callbacks with no extra parameters.
        (
            f"""\
from scrapy import Request, Spider


class MySpider(Spider):
    async def start(self):
        yield Request(url, self.parse_page, {AUTOMAP})

    def parse_page(self, response):
        pass
""",
            None,
        ),
        (
            f"""\
from scrapy import Request


def parse():
    pass


Request(url, {AUTOMAP})
""",
            None,
        ),
        # Callbacks that cannot be resolved.
        (
            f"""\
from scrapy import Request, Spider


class MySpider(Spider):
    async def start(self):
        yield Request(url, self.parse_page, {AUTOMAP})
""",
            None,
        ),
        (
            f"""\
from scrapy import Request, Spider


class MySpider(Spider):
    async def start(self):
        yield Request(url, None, {AUTOMAP})
""",
            None,
        ),
        # replace() keeps the callback of the original request.
        (
            f"""\
from scrapy import Spider
from scrapy_poet import DummyResponse


class MySpider(Spider):
    def parse(self, response: DummyResponse):
        yield response.request.replace({AUTOMAP})
""",
            None,
        ),
        # Meta that does not enable automatic mapping.
        (
            """\
from scrapy import Request, Spider
from scrapy_poet import DummyResponse


class MySpider(Spider):
    async def start(self):
        yield Request(url, self.parse, meta={"zyte_api_automap": True, key: "value"})

    def parse(self, response: DummyResponse):
        pass
""",
            None,
        ),
    )
)


@cases(CALLBACK_CASES)
def test_callbacks(
    files: File | list[File],
    expected: ExpectedIssue | list[ExpectedIssue] | None,
    options,
):
    check_project(files, expected, options)
