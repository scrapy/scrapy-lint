from __future__ import annotations

import ast
from inspect import cleandoc

import pytest

from scrapy_lint.finders.domains import UrlInAllowedDomainsIssueFinder
from scrapy_lint.finders.spiders import UnneededStartIssueFinder
from scrapy_lint.fixes import Edit, apply_edits
from scrapy_lint.issues import Pos

from . import File
from .helpers import fix_project

PATH = "a.py"


# (source, expected output, number of edits applied)
CASES = (
    # SCP02: a single URL in a list becomes its bare domain.
    (
        'allowed_domains = ["https://toscrape.com/"]\n',
        'allowed_domains = ["toscrape.com"]\n',
        1,
    ),
    # Tuples are fixed too.
    (
        'allowed_domains = ("https://toscrape.com/",)\n',
        'allowed_domains = ("toscrape.com",)\n',
        1,
    ),
    # The original quote style is preserved.
    (
        "allowed_domains = ['https://toscrape.com/']\n",
        "allowed_domains = ['toscrape.com']\n",
        1,
    ),
    # Paths, queries and ports are dropped; only the host remains.
    (
        'allowed_domains = ["http://example.com:8080/a?b=c"]\n',
        'allowed_domains = ["example.com"]\n',
        1,
    ),
    # Every URL in the list is fixed; already-bare domains are left alone.
    (
        cleandoc(
            """
            class MySpider(Spider):
                allowed_domains = [
                    "a.example",
                    "https://b.example/path",
                    "https://c.example",
                ]
            """,
        )
        + "\n",
        cleandoc(
            """
            class MySpider(Spider):
                allowed_domains = [
                    "a.example",
                    "b.example",
                    "c.example",
                ]
            """,
        )
        + "\n",
        2,
    ),
    # A flagged value without a usable host is reported but left untouched.
    (
        'allowed_domains = ["mailto:hi@toscrape.com"]\n',
        'allowed_domains = ["mailto:hi@toscrape.com"]\n',
        0,
    ),
    # Non-string elements are skipped; the URL alongside them is still fixed.
    (
        'allowed_domains = [None, "https://toscrape.com/"]\n',
        'allowed_domains = [None, "toscrape.com"]\n',
        1,
    ),
    # A prefixed string literal (e.g. raw) is reported but not rewritten.
    (
        'allowed_domains = [r"https://toscrape.com/"]\n',
        'allowed_domains = [r"https://toscrape.com/"]\n',
        0,
    ),
    # A quote character inside the host blocks the rewrite.
    (
        "allowed_domains = ['http://ex\\'ample.com/']\n",
        "allowed_domains = ['http://ex\\'ample.com/']\n",
        0,
    ),
    # SCP53: a start method becomes start_urls, keeping the quote style.
    (
        cleandoc(
            """
            class MySpider(Spider):
                name = "my"

                async def start(self):
                    yield Request('https://a.example/', dont_filter=True)
                    yield Request("https://b.example/", dont_filter=True)
            """,
        )
        + "\n",
        cleandoc(
            """
            class MySpider(Spider):
                name = "my"

                start_urls = ['https://a.example/', "https://b.example/"]
            """,
        )
        + "\n",
        1,
    ),
    # URLs that do not fit in a single line get one line each.
    (
        cleandoc(
            """
            class MySpider(Spider):
                async def start(self):
                    for url in ["https://a.example/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"]:
                        yield Request(url, dont_filter=True)
            """,
        )
        + "\n",
        cleandoc(
            """
            class MySpider(Spider):
                start_urls = [
                    "https://a.example/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                ]
            """,
        )
        + "\n",
        1,
    ),
    # A method that only re-sends start_urls is removed, blank lines included.
    (
        cleandoc(
            """
            class MySpider(Spider):
                name = "my"
                start_urls = ["https://toscrape.com/"]

                async def start(self):
                    for url in self.start_urls:
                        yield Request(url, dont_filter=True)
            """,
        )
        + "\n",
        cleandoc(
            """
            class MySpider(Spider):
                name = "my"
                start_urls = ["https://toscrape.com/"]
            """,
        )
        + "\n",
        1,
    ),
    # Removing the first statement of a class body does not leave a blank line.
    (
        cleandoc(
            """
            class MySpider(Spider):
                async def start(self):
                    for url in self.start_urls:
                        yield Request(url, dont_filter=True)

                def parse(self, response): ...
            """,
        )
        + "\n",
        cleandoc(
            """
            class MySpider(Spider):
                def parse(self, response): ...
            """,
        )
        + "\n",
        1,
    ),
    # Removing the only statement of a class body would break it.
    (
        cleandoc(
            """
            class MySpider(Spider):
                async def start(self):
                    for url in self.start_urls:
                        yield Request(url, dont_filter=True)
            """,
        )
        + "\n",
        cleandoc(
            """
            class MySpider(Spider):
                async def start(self):
                    for url in self.start_urls:
                        yield Request(url, dont_filter=True)
            """,
        )
        + "\n",
        0,
    ),
    # Without dont_filter the rewrite would enable duplicate filtering.
    (
        cleandoc(
            """
            class MySpider(Spider):
                name = "my"

                async def start(self):
                    yield Request("https://toscrape.com/")
            """,
        )
        + "\n",
        cleandoc(
            """
            class MySpider(Spider):
                name = "my"

                async def start(self):
                    yield Request("https://toscrape.com/")
            """,
        )
        + "\n",
        0,
    ),
    # A start_urls attribute leaves no room for the rewrite.
    (
        cleandoc(
            """
            class MySpider(Spider):
                start_urls: list[str] = ["https://a.example/"]

                async def start(self):
                    yield Request("https://b.example/", dont_filter=True)
            """,
        )
        + "\n",
        cleandoc(
            """
            class MySpider(Spider):
                start_urls: list[str] = ["https://a.example/"]

                async def start(self):
                    yield Request("https://b.example/", dont_filter=True)
            """,
        )
        + "\n",
        0,
    ),
    # A prefixed string literal is reported but not rewritten.
    (
        cleandoc(
            """
            class MySpider(Spider):
                name = "my"

                async def start(self):
                    yield Request(r"https://toscrape.com/", dont_filter=True)
            """,
        )
        + "\n",
        cleandoc(
            """
            class MySpider(Spider):
                name = "my"

                async def start(self):
                    yield Request(r"https://toscrape.com/", dont_filter=True)
            """,
        )
        + "\n",
        0,
    ),
)


@pytest.mark.parametrize(("source", "expected", "fixed"), CASES, ids=range(len(CASES)))
def test_fix(source: str, expected: str, fixed: int):
    fix_project(
        File(source, path=PATH),
        File(expected, path=PATH),
        expected_fixed=fixed,
    )


def test_apply_edits_empty():
    source = "allowed_domains = []\n"
    assert apply_edits(source, []) == (source, 0)


def test_apply_edits_skips_overlap():
    source = "abcdef\n"
    # Two edits over overlapping ranges; only the later (back-to-front) one applies.
    edits = [
        Edit(start=Pos(1, 0), end=Pos(1, 4), replacement="X"),
        Edit(start=Pos(1, 2), end=Pos(1, 6), replacement="Y"),
    ]
    new_source, applied = apply_edits(source, edits)
    assert applied == 1
    assert new_source == "abY\n"


def test_build_fix_without_source():
    finder = UrlInAllowedDomainsIssueFinder()
    stmt = ast.parse('"https://toscrape.com/"').body[0]
    assert isinstance(stmt, ast.Expr)
    elt = stmt.value
    assert isinstance(elt, ast.Constant)
    assert isinstance(elt.value, str)
    assert finder.build_fix(elt, elt.value) is None


def test_build_start_fix_without_source():
    source = cleandoc(
        """
        class MySpider(Spider):
            name = "my"

            async def start(self):
                yield Request("https://toscrape.com/", dont_filter=True)
        """,
    )
    node = ast.parse(source).body[0]
    assert isinstance(node, ast.ClassDef)
    issues = list(UnneededStartIssueFinder()(node))
    assert len(issues) == 1
    assert issues[0].fix is None
