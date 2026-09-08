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
)


@pytest.mark.parametrize(("source", "expected", "fixed"), CASES, ids=range(len(CASES)))
def test_fix(source: str, expected: str, fixed: int):
    fix_project(
        File(source, path=PATH),
        File(expected, path=PATH),
        expected_fixed=fixed,
    )


REQUIREMENTS = "scrapy==2.13.0\nscrapy-poet==0.26.0\nzyte-spider-templates==0.12.0\n"
ADDONS = "ADDONS = {\n    scrapy_poet.Addon: 300,\n    zyte_spider_templates.Addon: 1000,\n}\n"
IMPORTS = "import scrapy_poet\nimport zyte_spider_templates\n"

# SCP47: (source, expected output, number of edits applied)
ADDON_CASES = (
    # A missing ADDONS setting is defined at the end of the file.
    (
        'USER_AGENT = "x"\n',
        f'{IMPORTS}USER_AGENT = "x"\n\n{ADDONS}',
        2,
    ),
    # An empty file gets no leading blank line.
    (
        "",
        f"{IMPORTS}{ADDONS}",
        2,
    ),
    # Imports go below the module docstring.
    (
        '"""Doc."""\n',
        f'"""Doc."""\n{IMPORTS}\n{ADDONS}',
        2,
    ),
    # Imports go below existing imports, including relative ones.
    (
        "from . import base\n",
        f"from . import base\n{IMPORTS}\n{ADDONS}",
        2,
    ),
    # Add-ons are added to an existing ADDONS setting, keeping its style.
    (
        "import scrapy_poet\n\nADDONS = {\n    scrapy_poet.Addon: 300,\n}\n",
        "import scrapy_poet\nimport zyte_spider_templates\n\nADDONS = {\n"
        "    scrapy_poet.Addon: 300,\n    zyte_spider_templates.Addon: 1000,\n}\n",
        2,
    ),
    (
        "ADDONS = {}\n",
        f"{IMPORTS}{ADDONS}",
        2,
    ),
    # Add-ons already imported are used through their existing name.
    (
        "import scrapy_poet\n",
        "import scrapy_poet\nimport zyte_spider_templates\n\n"
        "ADDONS = {\n    scrapy_poet.Addon: 300,\n"
        "    zyte_spider_templates.Addon: 1000,\n}\n",
        2,
    ),
    (
        "from scrapy_poet import Addon\n",
        "from scrapy_poet import Addon\nimport zyte_spider_templates\n\n"
        "ADDONS = {\n    Addon: 300,\n"
        "    zyte_spider_templates.Addon: 1000,\n}\n",
        2,
    ),
    (
        "from scrapy_poet import Addon\n\nADDONS = {Addon: 300}\n",
        "from scrapy_poet import Addon\nimport zyte_spider_templates\n\n"
        "ADDONS = {Addon: 300,\n          zyte_spider_templates.Addon: 1000}\n",
        2,
    ),
    # An ADDONS setting that is not a dict literal is reported but left
    # untouched.
    (
        "ADDONS = dict()\n",
        "ADDONS = dict()\n",
        0,
    ),
    (
        "BASE = {}\nADDONS = {**BASE}\n",
        "BASE = {}\nADDONS = {**BASE}\n",
        0,
    ),
    # So is an ADDONS setting defined outside the module level.
    (
        "if True:\n    ADDONS = {}\n",
        "if True:\n    ADDONS = {}\n",
        0,
    ),
)


@pytest.mark.parametrize(
    ("source", "expected", "fixed"),
    ADDON_CASES,
    ids=range(len(ADDON_CASES)),
)
def test_fix_missing_addons(source: str, expected: str, fixed: int):
    fix_project(
        (
            File("[settings]\na=a", path="scrapy.cfg"),
            File(REQUIREMENTS, path="requirements.txt"),
            File(source, path=PATH),
        ),
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
