from __future__ import annotations

import ast
from inspect import cleandoc
from pathlib import Path

import pytest

from scrapy_lint.context import Context, Project
from scrapy_lint.data.apis import API_PARAMETERS
from scrapy_lint.data.packages import PACKAGES
from scrapy_lint.finders.apis import APIIssueFinder
from scrapy_lint.finders.domains import UrlInAllowedDomainsIssueFinder
from scrapy_lint.fixes import Edit, apply_edits
from scrapy_lint.issues import Pos

from . import File
from .helpers import fix_project

PATH = "a.py"
SCRAPY_HIGHEST_KNOWN = PACKAGES["scrapy"].highest_known_version


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
)


@pytest.mark.parametrize(("source", "expected", "fixed"), CASES, ids=range(len(CASES)))
def test_fix(source: str, expected: str, fixed: int):
    fix_project(
        File(source, path=PATH),
        File(expected, path=PATH),
        expected_fixed=fixed,
    )


# (source, expected output) for SCP48, where the removed argument is dropped
# together with the comma that separates it from a neighboring argument.
API_CASES = (
    (
        "PythonItemExporter(binary=False)\n",
        "PythonItemExporter()\n",
    ),
    (
        "PythonItemExporter(binary=False, indent=2)\n",
        "PythonItemExporter(indent=2)\n",
    ),
    (
        "PythonItemExporter(indent=2, binary=False)\n",
        "PythonItemExporter(indent=2)\n",
    ),
    (
        "PythonItemExporter(indent=2, binary =  False)\n",
        "PythonItemExporter(indent=2)\n",
    ),
    (
        "PythonItemExporter(binary=False,)\n",
        "PythonItemExporter()\n",
    ),
    # An argument that has a line to itself takes the whole line with it.
    (
        cleandoc(
            """
            PythonItemExporter(
                binary=False,
                indent=2,
            )
            """,
        )
        + "\n",
        cleandoc(
            """
            PythonItemExporter(
                indent=2,
            )
            """,
        )
        + "\n",
    ),
    (
        cleandoc(
            """
            PythonItemExporter(
                indent=2,
                binary=False
            )
            """,
        )
        + "\n",
        cleandoc(
            """
            PythonItemExporter(
                indent=2,
            )
            """,
        )
        + "\n",
    ),
    # A parenthesized value is removed along with its parentheses.
    (
        cleandoc(
            """
            PythonItemExporter(binary=(
                False
            ), indent=2)
            """,
        )
        + "\n",
        "PythonItemExporter(indent=2)\n",
    ),
    # Values that cannot be resolved statically are removed as well: on these
    # Scrapy versions the parameter is gone whatever its value.
    (
        "PythonItemExporter(binary=flag)\n",
        "PythonItemExporter()\n",
    ),
)


@pytest.mark.parametrize(
    ("source", "expected"),
    API_CASES,
    ids=range(len(API_CASES)),
)
def test_fix_removed_api(source: str, expected: str):
    fix_project(
        (
            File("", path="scrapy.cfg"),
            File(f"scrapy=={SCRAPY_HIGHEST_KNOWN}", path="requirements.txt"),
            File(source, path=PATH),
        ),
        File(expected, path=PATH),
        expected_fixed=1,
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


def test_build_api_fix_without_source():
    finder = APIIssueFinder(Context(Project(Path.cwd())))
    stmt = ast.parse("PythonItemExporter(binary=False)").body[0]
    assert isinstance(stmt, ast.Expr)
    assert isinstance(stmt.value, ast.Call)
    kw = stmt.value.keywords[0]
    assert finder.build_fix(API_PARAMETERS[0], kw) is None


def test_build_fix_without_source():
    finder = UrlInAllowedDomainsIssueFinder()
    stmt = ast.parse('"https://toscrape.com/"').body[0]
    assert isinstance(stmt, ast.Expr)
    elt = stmt.value
    assert isinstance(elt, ast.Constant)
    assert isinstance(elt.value, str)
    assert finder.build_fix(elt, elt.value) is None
