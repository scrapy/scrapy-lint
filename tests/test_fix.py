from __future__ import annotations

import ast
from inspect import cleandoc
from pathlib import Path

import pytest

from scrapy_lint.ast import iter_dict
from scrapy_lint.context import Context, Project
from scrapy_lint.data.packages import PACKAGES
from scrapy_lint.finders.domains import UrlInAllowedDomainsIssueFinder
from scrapy_lint.finders.methods import DeprecatedArgumentIssueFinder
from scrapy_lint.finders.settings.types import build_sort_fix
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
    # Only the port is dropped from a domain that carries one.
    (
        'allowed_domains = ["toscrape.com:8080", "127.0.0.1:8080"]\n',
        'allowed_domains = ["toscrape.com", "127.0.0.1"]\n',
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
    # SCP06: extract_first() becomes get(), keeping any arguments.
    (
        'response.css("a").extract_first(default="")\n',
        'response.css("a").get(default="")\n',
        1,
    ),
    # SCP68: extract() becomes getall().
    (
        'response.css("a").extract()\n',
        'response.css("a").getall()\n',
        1,
    ),
    # The call may span several lines.
    (
        cleandoc(
            """
            values = response.css(
                "a",
            ).extract()
            """,
        )
        + "\n",
        cleandoc(
            """
            values = response.css(
                "a",
            ).getall()
            """,
        )
        + "\n",
        1,
    ),
    # SCP60: entries are sorted by priority, and the layout is kept.
    (
        'settings["DOWNLOADER_MIDDLEWARES"] = {"a.B": 200, "c.D": 100}\n',
        'settings["DOWNLOADER_MIDDLEWARES"] = {"c.D": 100, "a.B": 200}\n',
        1,
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
    # SCP78: the call is rewritten and the import added after the last import.
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
    # SCP70: module-level and root loggers become self.logger.
    (
        cleandoc(
            """
            logger = logging.getLogger(__name__)


            class MySpider(Spider):
                def parse(self, response):
                    logger.info("a")
                    logging.warning("b")
            """,
        )
        + "\n",
        cleandoc(
            """
            logger = logging.getLogger(__name__)


            class MySpider(Spider):
                def parse(self, response):
                    self.logger.info("a")
                    self.logger.warning("b")
            """,
        )
        + "\n",
        2,
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


# (source, expected output, number of edits applied) for SCP51, where the
# deprecated parameter is dropped from the signature.
ARGUMENT_CASES = (
    (
        cleandoc(
            """
            class MyPipeline:
                def process_item(self, item, spider):
                    return item
            """,
        )
        + "\n",
        cleandoc(
            """
            class MyPipeline:
                def process_item(self, item):
                    return item
            """,
        )
        + "\n",
        1,
    ),
    # The annotation of the parameter goes with it.
    (
        cleandoc(
            """
            class MyPipeline:
                def open_spider(self, spider: Spider) -> None:
                    pass
            """,
        )
        + "\n",
        cleandoc(
            """
            class MyPipeline:
                def open_spider(self) -> None:
                    pass
            """,
        )
        + "\n",
        1,
    ),
    # A parameter that has a line to itself takes the whole line with it.
    (
        cleandoc(
            """
            class MyPipeline:
                async def process_spider_output(
                    self,
                    response,
                    result,
                    spider,
                ):
                    return result
            """,
        )
        + "\n",
        cleandoc(
            """
            class MyPipeline:
                async def process_spider_output(
                    self,
                    response,
                    result,
                ):
                    return result
            """,
        )
        + "\n",
        1,
    ),
    # Keyword-only parameters are dropped as long as the * marker keeps one.
    (
        cleandoc(
            """
            class MyPipeline:
                def process_item(self, item, *, spider, limit):
                    return item
            """,
        )
        + "\n",
        cleandoc(
            """
            class MyPipeline:
                def process_item(self, item, *, limit):
                    return item
            """,
        )
        + "\n",
        1,
    ),
    # Dropping the only keyword-only parameter would leave a dangling * marker.
    (
        cleandoc(
            """
            class MyPipeline:
                def process_item(self, item, *, spider):
                    return item
            """,
        )
        + "\n",
        cleandoc(
            """
            class MyPipeline:
                def process_item(self, item, *, spider):
                    return item
            """,
        )
        + "\n",
        0,
    ),
    # A method that uses the parameter is reported but left untouched.
    (
        cleandoc(
            """
            class MyPipeline:
                def process_item(self, item, spider):
                    spider.logger.info("Got an item")
                    return item
            """,
        )
        + "\n",
        cleandoc(
            """
            class MyPipeline:
                def process_item(self, item, spider):
                    spider.logger.info("Got an item")
                    return item
            """,
        )
        + "\n",
        0,
    ),
)


@pytest.mark.parametrize(
    ("source", "expected", "fixed"),
    ARGUMENT_CASES,
    ids=range(len(ARGUMENT_CASES)),
)
def test_fix_deprecated_argument(source: str, expected: str, fixed: int):
    fix_project(
        (
            File("", path="scrapy.cfg"),
            File(f"scrapy=={SCRAPY_HIGHEST_KNOWN}", path="requirements.txt"),
            File(source, path=PATH),
        ),
        File(expected, path=PATH),
        expected_fixed=fixed,
    )


# (source, expected output, number of edits applied) for SCP49 and SCP50,
# where a from-import statement can be pointed at the replacement module.
IMPORT_CASES = (
    (
        "from scrapy.utils.url import canonicalize_url\n",
        "from w3lib.url import canonicalize_url\n",
        1,
    ),
    # Every name of the statement moves to the same module in one edit, but
    # each deprecated name is still its own fixed issue.
    (
        "from scrapy.utils.url import canonicalize_url, is_url\n",
        "from w3lib.url import canonicalize_url, is_url\n",
        2,
    ),
    # An alias does not change the name of the imported object.
    (
        "from scrapy.utils.url import canonicalize_url as c\n",
        "from w3lib.url import canonicalize_url as c\n",
        1,
    ),
    # A name that has no replacement keeps the whole statement as it is.
    (
        "from scrapy.utils.url import canonicalize_url, escape_ajax\n",
        "from scrapy.utils.url import canonicalize_url, escape_ajax\n",
        0,
    ),
    # A replacement under a different name would leave the use sites broken.
    (
        "from scrapy.utils.versions import scrapy_components_versions\n",
        "from scrapy.utils.versions import scrapy_components_versions\n",
        0,
    ),
    # A module that does not follow the from keyword is left alone.
    (
        "from \\\n    scrapy.utils.url import canonicalize_url\n",
        "from \\\n    scrapy.utils.url import canonicalize_url\n",
        0,
    ),
)


@pytest.mark.parametrize(
    ("source", "expected", "fixed"),
    IMPORT_CASES,
    ids=range(len(IMPORT_CASES)),
)
def test_fix_import(source: str, expected: str, fixed: int):
    fix_project(
        (
            File("", path="scrapy.cfg"),
            File(f"scrapy=={SCRAPY_HIGHEST_KNOWN}", path="requirements.txt"),
            File(source, path=PATH),
        ),
        File(expected, path=PATH),
        expected_fixed=fixed,
    )


def spider_method(call: str) -> str:
    """Return a spider whose parse() method consists of *call*."""
    body = "".join(f"        {line}\n" for line in call.splitlines())
    return f"class MySpider(Spider):\n    def parse(self, response):\n{body}"


# (source, expected output, number of issues fixed) for Spider.log() calls,
# which become calls to the Spider.logger method of their level.
LOG_CASES = (
    ('self.log("a")', 'self.logger.debug("a")', 1),
    ('self.log(f"{response.url}")', 'self.logger.debug(f"{response.url}")', 1),
    ('self.log("a", level=logging.INFO)', 'self.logger.info("a")', 1),
    ('self.log("a", logging.WARNING)', 'self.logger.warning("a")', 1),
    ('self.log("a", level=WARN)', 'self.logger.warning("a")', 1),
    ('self.log("a", level=40)', 'self.logger.error("a")', 1),
    (
        'self.log("a", level=logging.CRITICAL, extra={"b": 1})',
        'self.logger.critical("a", extra={"b": 1})',
        1,
    ),
    (
        cleandoc(
            """
            self.log(
                "a",
                level=logging.INFO,
            )
            """,
        ),
        cleandoc(
            """
            self.logger.info(
                "a",
            )
            """,
        ),
        1,
    ),
    # Levels that are not a standard one, and arguments that cannot be told
    # apart, are left alone.
    *(
        (call, call, 0)
        for call in (
            'self.log("a", level=self.level)',
            'self.log("a", level=25)',
            "self.log(*args)",
            'self.log("a", logging.INFO, extra)',
            "self.log()",
        )
    ),
)


@pytest.mark.parametrize(
    ("source", "expected", "fixed"),
    LOG_CASES,
    ids=range(len(LOG_CASES)),
)
def test_fix_spider_log(source: str, expected: str, fixed: int):
    fix_project(
        (
            File("", path="scrapy.cfg"),
            File(f"scrapy=={SCRAPY_HIGHEST_KNOWN}", path="requirements.txt"),
            File(spider_method(source), path=PATH),
        ),
        File(spider_method(expected), path=PATH),
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


def test_build_sort_fix_without_source():
    stmt = ast.parse("{a: 2, b: 1}").body[0]
    assert isinstance(stmt, ast.Expr)
    node = stmt.value
    assert isinstance(node, ast.Dict)
    assert build_sort_fix(node, list(iter_dict(node)), [1, 0], None) is None


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
    assert finder.build_fix(elt, "toscrape.com", "replace URL with its domain") is None


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


def test_build_argument_fix_without_source():
    context = Context(Project(Path.cwd()))
    finder = DeprecatedArgumentIssueFinder(context)
    node = ast.parse("def process_item(self, item, spider): ...").body[0]
    assert isinstance(node, ast.FunctionDef)
    assert finder.build_fix(node, node.args.args[-1]) is None


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
