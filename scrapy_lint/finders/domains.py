import ast
from ast import (
    AST,
    AnnAssign,
    Assign,
    Attribute,
    ClassDef,
    Constant,
    List,
    Name,
    Tuple,
    expr,
)
from collections.abc import Generator
from urllib.parse import urlparse

from scrapy_lint.ast import definition_column
from scrapy_lint.fixes import Edit, Fix
from scrapy_lint.issues import (
    DISALLOWED_DOMAIN,
    NO_ALLOWED_DOMAINS,
    URL_IN_ALLOWED_DOMAINS,
    Issue,
    Pos,
)

SPIDER_BASES = frozenset(
    {
        "CSVFeedSpider",
        "CrawlSpider",
        "SitemapSpider",
        "Spider",
        "XMLFeedSpider",
    }
)


def get_list_metadata(node):
    return [
        (subnode.lineno, subnode.col_offset, subnode.value)
        for subnode in node.value.elts
        if isinstance(subnode, ast.Constant)
    ]


def is_list_assignment(node, var_name):
    return (
        isinstance(node.targets[0], ast.Name)
        and isinstance(node.value, (ast.List, ast.Tuple))
        and node.targets[0].id == var_name
    )


class UnreachableDomainIssueFinder:
    def __init__(self):
        self.allowed_domains = []
        self.start_urls = []
        self.reported = False

    def url_in_allowed_domains(self, url):
        netloc = urlparse(url).netloc
        return any(domain in netloc for _, _, domain in self.allowed_domains)

    def __call__(self, node) -> Generator[Issue]:
        if isinstance(node, ClassDef):
            self.allowed_domains = []
            self.start_urls = []
            self.reported = False
            return

        if self.reported:
            return

        if is_list_assignment(node, var_name="allowed_domains"):
            self.allowed_domains = get_list_metadata(node)

        if is_list_assignment(node, var_name="start_urls"):
            self.start_urls = get_list_metadata(node)

        if not all((self.allowed_domains, self.start_urls)):
            return

        for line, column, url in self.start_urls:
            if not self.url_in_allowed_domains(url):
                yield Issue(DISALLOWED_DOMAIN, Pos(line, column))

        self.reported = True


def assigned_names(node: ClassDef) -> Generator[str]:
    for statement in node.body:
        if isinstance(statement, AnnAssign):
            targets: list[expr] = [statement.target]
        elif isinstance(statement, Assign):
            targets = statement.targets
        else:
            continue
        for target in targets:
            if isinstance(target, Name):
                yield target.id


def is_spider_base(node: AST) -> bool:
    if isinstance(node, Attribute):
        return node.attr in SPIDER_BASES
    return isinstance(node, Name) and node.id in SPIDER_BASES


def find_no_allowed_domains_issues(node: AST) -> Generator[Issue]:
    assert isinstance(node, ClassDef)
    if not any(is_spider_base(base) for base in node.bases):
        return
    names = set(assigned_names(node))
    if "start_urls" in names and "allowed_domains" not in names:
        yield Issue(NO_ALLOWED_DOMAINS, Pos(node.lineno, definition_column(node)))


class UrlInAllowedDomainsIssueFinder:
    def __init__(self, source: str | None = None):
        self.source = source

    def __call__(self, node: AST) -> Generator[Issue]:
        if not is_list_assignment(node, var_name="allowed_domains"):
            return
        assert isinstance(node, Assign)
        assert isinstance(node.value, (List, Tuple))
        for elt in node.value.elts:
            if not (isinstance(elt, Constant) and isinstance(elt.value, str)):
                continue
            if not self.is_url(elt.value):
                continue
            pos = Pos(elt.lineno, elt.col_offset)
            yield Issue(URL_IN_ALLOWED_DOMAINS, pos, fix=self.build_fix(elt, elt.value))

    def build_fix(self, elt: Constant, url: str) -> Fix | None:
        """Build a fix that replaces a URL literal with its bare domain.

        Returns ``None`` (report only, no fix) when the rewrite cannot be made
        safely: no parseable host, a non-plain string literal (prefix or
        triple-quote), or a quote character that appears inside the host.
        """
        if self.source is None:
            return None
        host = urlparse(url).hostname
        if not host:
            return None
        segment = ast.get_source_segment(self.source, elt)
        if not segment or segment[0] not in {'"', "'"} or segment[-1] != segment[0]:
            return None
        quote = segment[0]
        if quote in host:
            return None
        assert elt.end_lineno is not None
        assert elt.end_col_offset is not None
        edit = Edit(
            start=Pos(elt.lineno, elt.col_offset),
            end=Pos(elt.end_lineno, elt.end_col_offset),
            replacement=f"{quote}{host}{quote}",
        )
        return Fix([edit], message="replace URL with its domain")

    def is_url(self, domain):
        # when it's just a domain (as 'toscrape.com'), the parsed URL contains
        # only the 'path' component
        forbidden_components = [
            "scheme",
            "netloc",
            "params",
            "query",
            "fragment",
        ]
        parts = urlparse(domain)
        return any(getattr(parts, comp, None) for comp in forbidden_components)
