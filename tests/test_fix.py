from __future__ import annotations

import ast
from inspect import cleandoc

import pytest

from scrapy_lint.finders.domains import UrlInAllowedDomainsIssueFinder
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
    # SCP47: the call is rewritten and the import added after the last import.
    (
        cleandoc(
            """
            from urllib.parse import urlparse

            import scrapy


            class MySpider(scrapy.Spider):
                def parse(self, response):
                    yield {"netloc": urlparse(response.url).netloc}
            """,
        )
        + "\n",
        cleandoc(
            """
            from urllib.parse import urlparse

            import scrapy
            from scrapy.utils.httpobj import urlparse_cached


            class MySpider(scrapy.Spider):
                def parse(self, response):
                    yield {"netloc": urlparse_cached(response).netloc}
            """,
        )
        + "\n",
        1,
    ),
    # Several calls in the same file share a single import insertion.
    (
        cleandoc(
            """
            from urllib.parse import urlparse


            def parse(request, response):
                return urlparse(request.url), urlparse(response.url)
            """,
        )
        + "\n",
        cleandoc(
            """
            from urllib.parse import urlparse
            from scrapy.utils.httpobj import urlparse_cached


            def parse(request, response):
                return urlparse_cached(request), urlparse_cached(response)
            """,
        )
        + "\n",
        2,
    ),
    # An existing import is reused.
    (
        cleandoc(
            """
            from urllib.parse import urlparse

            from scrapy.utils.httpobj import urlparse_cached


            def parse(request, response):
                return urlparse(response.url), urlparse_cached(request)
            """,
        )
        + "\n",
        cleandoc(
            """
            from urllib.parse import urlparse

            from scrapy.utils.httpobj import urlparse_cached


            def parse(request, response):
                return urlparse_cached(response), urlparse_cached(request)
            """,
        )
        + "\n",
        1,
    ),
    # Without a top-level import to add the new one after, the call is reported
    # but left untouched.
    (
        cleandoc(
            """
            def parse(response):
                from urllib.parse import urlparse

                return urlparse(response.url)
            """,
        )
        + "\n",
        cleandoc(
            """
            def parse(response):
                from urllib.parse import urlparse

                return urlparse(response.url)
            """,
        )
        + "\n",
        0,
    ),
    # Neither is it fixed when the last import leaves no line to insert into.
    (
        cleandoc(
            """
            def parse(response):
                return urlparse(response.url)


            from urllib.parse import urlparse
            """,
        )
        + "\n",
        cleandoc(
            """
            def parse(response):
                return urlparse(response.url)


            from urllib.parse import urlparse
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
    assert apply_edits(source, []) == (source, [])


def test_apply_edits_skips_overlap():
    source = "abcdef\n"
    # Two edits over overlapping ranges; only the later (back-to-front) one applies.
    edits = [
        Edit(start=Pos(1, 0), end=Pos(1, 4), replacement="X"),
        Edit(start=Pos(1, 2), end=Pos(1, 6), replacement="Y"),
    ]
    new_source, applied = apply_edits(source, edits)
    assert applied == [edits[1]]
    assert new_source == "abY\n"


def test_apply_edits_skips_repeats():
    source = "abcdef\n"
    insert = Edit(start=Pos(1, 0), end=Pos(1, 0), replacement="X")
    new_source, applied = apply_edits(source, [insert, insert])
    assert applied == [insert]
    assert new_source == "Xabcdef\n"


def test_build_fix_without_source():
    finder = UrlInAllowedDomainsIssueFinder()
    stmt = ast.parse('"https://toscrape.com/"').body[0]
    assert isinstance(stmt, ast.Expr)
    elt = stmt.value
    assert isinstance(elt, ast.Constant)
    assert isinstance(elt.value, str)
    assert finder.build_fix(elt, elt.value) is None
