from __future__ import annotations

import ast
from inspect import cleandoc

import pytest

from scrapy_lint.ast import iter_dict
from scrapy_lint.finders.domains import UrlInAllowedDomainsIssueFinder
from scrapy_lint.finders.settings.types import build_sort_fix
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
    # SCP47: entries are sorted by priority, and the layout is kept.
    (
        'settings["DOWNLOADER_MIDDLEWARES"] = {"a.B": 200, "c.D": 100}\n',
        'settings["DOWNLOADER_MIDDLEWARES"] = {"c.D": 100, "a.B": 200}\n',
        1,
    ),
)


@pytest.mark.parametrize(("source", "expected", "fixed"), CASES, ids=range(len(CASES)))
def test_fix(source: str, expected: str, fixed: int):
    fix_project(
        File(source, path=PATH),
        File(expected, path=PATH),
        expected_fixed=fixed,
    )


CONFIG = File("[settings]\ndefault = settings", path="scrapy.cfg")
SETTING_MODULE_PATH = "settings.py"

# (source, expected output, number of edits applied)
SETTING_MODULE_CASES = (
    # Entries move as a whole, keeping their own lines and their indentation.
    (
        cleandoc(
            """
            EXTENSIONS = {
                "a.B": 900,
                "c.D": 0,
            }
            """,
        )
        + "\n",
        cleandoc(
            """
            EXTENSIONS = {
                "c.D": 0,
                "a.B": 900,
            }
            """,
        )
        + "\n",
        1,
    ),
    # Disabled components go first.
    (
        'ADDONS = {"a.B": 100, "c.D": None}\n',
        'ADDONS = {"c.D": None, "a.B": 100}\n',
        1,
    ),
    # A comment inside the dict is reported but not rewritten, since the comment
    # would stay behind while the entry it documents moves.
    (
        'EXTENSIONS = {\n    "a.B": 900,  # first\n    "c.D": 0,\n}\n',
        'EXTENSIONS = {\n    "a.B": 900,  # first\n    "c.D": 0,\n}\n',
        0,
    ),
)


@pytest.mark.parametrize(
    ("source", "expected", "fixed"),
    SETTING_MODULE_CASES,
    ids=range(len(SETTING_MODULE_CASES)),
)
def test_fix_setting_module(source: str, expected: str, fixed: int):
    fix_project(
        [CONFIG, File(source, path=SETTING_MODULE_PATH)],
        File(expected, path=SETTING_MODULE_PATH),
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


def test_build_sort_fix_without_source():
    stmt = ast.parse("{a: 2, b: 1}").body[0]
    assert isinstance(stmt, ast.Expr)
    node = stmt.value
    assert isinstance(node, ast.Dict)
    assert build_sort_fix(node, list(iter_dict(node)), [1, 0], None) is None


def test_build_fix_without_source():
    finder = UrlInAllowedDomainsIssueFinder()
    stmt = ast.parse('"https://toscrape.com/"').body[0]
    assert isinstance(stmt, ast.Expr)
    elt = stmt.value
    assert isinstance(elt, ast.Constant)
    assert isinstance(elt.value, str)
    assert finder.build_fix(elt, elt.value) is None
