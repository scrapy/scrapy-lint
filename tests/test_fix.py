from __future__ import annotations

import ast
from inspect import cleandoc

import pytest

from scrapy_lint.data.packages import PACKAGES
from scrapy_lint.finders.domains import UrlInAllowedDomainsIssueFinder
from scrapy_lint.finders.spiders import StartUrlIssueFinder, UnneededStartIssueFinder
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
    # SCP54: a start method becomes start_urls, keeping the quote style.
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
    # SCP58: a documentation comment becomes a docstring below the field.
    (
        cleandoc(
            """
            class ProductItem(scrapy.Item):
                #: Product name.
                name = scrapy.Field()
            """,
        )
        + "\n",
        cleandoc(
            """
            class ProductItem(scrapy.Item):
                name = scrapy.Field()
                \"\"\"Product name.\"\"\"
            """,
        )
        + "\n",
        1,
    ),
    # Each line of a multi-line block becomes a line of the docstring.
    (
        cleandoc(
            """
            @dataclass
            class Product:
                #: Product name,
                #: as advertised.
                name: str
            """,
        )
        + "\n",
        cleandoc(
            """
            @dataclass
            class Product:
                name: str
                \"\"\"Product name,
                as advertised.\"\"\"
            """,
        )
        + "\n",
        1,
    ),
    # A field whose value spans several lines keeps its layout.
    (
        cleandoc(
            """
            class ProductItem(scrapy.Item):
                #: Product name.
                name = scrapy.Field(
                    serializer=str,
                )
            """,
        )
        + "\n",
        cleandoc(
            """
            class ProductItem(scrapy.Item):
                name = scrapy.Field(
                    serializer=str,
                )
                \"\"\"Product name.\"\"\"
            """,
        )
        + "\n",
        1,
    ),
    # A trailing documentation comment is reported but not rewritten.
    (
        "class ProductItem(scrapy.Item):\n    name = scrapy.Field()  #: Product name.\n",
        "class ProductItem(scrapy.Item):\n    name = scrapy.Field()  #: Product name.\n",
        0,
    ),
    # A field that already has a docstring is reported but not rewritten.
    (
        cleandoc(
            """
            class ProductItem(scrapy.Item):
                #: Product name.
                name = scrapy.Field()
                \"\"\"Product name.\"\"\"
            """,
        )
        + "\n",
        cleandoc(
            """
            class ProductItem(scrapy.Item):
                #: Product name.
                name = scrapy.Field()
                \"\"\"Product name.\"\"\"
            """,
        )
        + "\n",
        0,
    ),
    # Comment text that cannot be quoted as a docstring blocks the rewrite.
    (
        'class ProductItem(scrapy.Item):\n    #: Name, e.g. "Chair"\n    name = scrapy.Field()\n',
        'class ProductItem(scrapy.Item):\n    #: Name, e.g. "Chair"\n    name = scrapy.Field()\n',
        0,
    ),
    # SCP67: a string start_url is renamed and wrapped in a list.
    (
        cleandoc(
            """
            class MySpider(Spider):
                start_url = "https://toscrape.com"
            """,
        )
        + "\n",
        cleandoc(
            """
            class MySpider(Spider):
                start_urls = ["https://toscrape.com"]
            """,
        )
        + "\n",
        1,
    ),
    # A sequence value is renamed without being wrapped.
    (
        'class MySpider(Spider):\n    start_url = ("https://toscrape.com",)\n',
        'class MySpider(Spider):\n    start_urls = ("https://toscrape.com",)\n',
        1,
    ),
    # A value that could be either a URL or a sequence of URLs is not rewritten.
    (
        "class MySpider(Spider):\n    start_url = URL\n",
        "class MySpider(Spider):\n    start_url = URL\n",
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


# (source, expected output) for SCP75, where the removed argument is dropped
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


def test_build_start_url_fix_without_source():
    finder = StartUrlIssueFinder()
    statement = ast.parse('start_url = "https://toscrape.com"').body[0]
    assert isinstance(statement, ast.Assign)
    assert finder.build_fix(statement) is None


# (source, expected output) for SCP28 and SCP30, where a deprecated or removed
# setting is renamed as the setting that replaces it.
SETTING_CASES = (
    (
        'settings["CONCURRENT_REQUESTS_PER_IP"]\n',
        'settings["CONCURRENT_REQUESTS_PER_DOMAIN"]\n',
    ),
    # The original quote style is preserved.
    (
        "settings.getint('CONCURRENT_REQUESTS_PER_IP')\n",
        "settings.getint('CONCURRENT_REQUESTS_PER_DOMAIN')\n",
    ),
    (
        'settings.update({"CONCURRENT_REQUESTS_PER_IP": 1})\n',
        'settings.update({"CONCURRENT_REQUESTS_PER_DOMAIN": 1})\n',
    ),
    # A removed setting is renamed as well.
    (
        'settings["REDIRECT_MAX_METAREFRESH_DELAY"]\n',
        'settings["METAREFRESH_MAXDELAY"]\n',
    ),
    # A literal that is not a plain, single-line string is left alone.
    (
        'settings["""CONCURRENT_REQUESTS_PER_IP"""]\n',
        'settings["""CONCURRENT_REQUESTS_PER_IP"""]\n',
    ),
)


@pytest.mark.parametrize(
    ("source", "expected"),
    SETTING_CASES,
    ids=range(len(SETTING_CASES)),
)
def test_fix_renamed_setting(source: str, expected: str):
    fix_project(
        (
            File("", path="scrapy.cfg"),
            File(f"scrapy=={SCRAPY_HIGHEST_KNOWN}", path="requirements.txt"),
            File(source, path=PATH),
        ),
        File(expected, path=PATH),
        expected_fixed=int(source != expected),
    )


def test_fix_renamed_setting_in_setting_module():
    fix_project(
        (
            File("[settings]\ndefault = a", path="scrapy.cfg"),
            File(f"scrapy=={SCRAPY_HIGHEST_KNOWN}", path="requirements.txt"),
            File("CONCURRENT_REQUESTS_PER_IP = 1\n", path=PATH),
        ),
        File("CONCURRENT_REQUESTS_PER_DOMAIN = 1\n", path=PATH),
        expected_fixed=1,
    )


def test_deprecated_setting_without_replacement_is_not_fixed():
    fix_project(
        (
            File("", path="scrapy.cfg"),
            File(f"scrapy=={SCRAPY_HIGHEST_KNOWN}", path="requirements.txt"),
            File('settings["FEED_URI"]\n', path=PATH),
        ),
        File('settings["FEED_URI"]\n', path=PATH),
        expected_fixed=0,
    )
