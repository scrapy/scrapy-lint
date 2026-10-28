from __future__ import annotations

import ast
from ast import (
    AST,
    Assign,
    Attribute,
    Call,
    Constant,
    Import,
    ImportFrom,
    Module,
    Subscript,
)
from typing import TYPE_CHECKING

from scrapy_lint.fixes import Edit, Fix
from scrapy_lint.issues import (
    ABSOLUTE_NESTED_XPATH,
    IMPROPER_FIRST_MATCH_EXTRACTION,
    IMPROPER_RESPONSE_SELECTOR,
    IMPROPER_RESPONSE_URL_JOIN,
    OLD_SELECTOR_GETTER,
    UNCACHED_URLPARSE,
    Issue,
    Pos,
)

if TYPE_CHECKING:
    from collections.abc import Generator


def find_url_join_issues(node: AST) -> Generator[Issue]:
    assert isinstance(node, Call)
    if not (
        isinstance(node.func, ast.Name) and node.func.id == "urljoin" and node.args
    ):
        return
    first_param = node.args[0]
    if not isinstance(first_param, ast.Attribute) or not isinstance(
        first_param.value,
        ast.Name,
    ):
        return
    if first_param.value.id == "response" and first_param.attr == "url":
        yield Issue(IMPROPER_RESPONSE_URL_JOIN, Pos.from_node(node))


_CACHED_URLPARSE_IMPORT = "from scrapy.utils.httpobj import urlparse_cached\n"
_URLPARSE_TARGETS = frozenset({"request", "response"})


def _get_urlparse_target(node: Call) -> str | None:
    """Return the name of the request or response whose URL *node* parses, or
    ``None`` if *node* is not such a call.
    """
    if not (
        isinstance(node.func, ast.Name)
        and node.func.id == "urlparse"
        and len(node.args) == 1
        and not node.keywords
    ):
        return None
    arg = node.args[0]
    if not (isinstance(arg, Attribute) and arg.attr == "url"):
        return None
    if not (isinstance(arg.value, ast.Name) and arg.value.id in _URLPARSE_TARGETS):
        return None
    return arg.value.id


def _binds_urlparse_cached(node: Import | ImportFrom) -> bool:
    return any(
        (alias_.asname or alias_.name) == "urlparse_cached" for alias_ in node.names
    )


class UrlparseIssueFinder:
    def __init__(self, tree: Module, source: str):
        self.import_edit: Edit | None = None
        self.fixable = False
        imports = [node for node in tree.body if isinstance(node, (Import, ImportFrom))]
        if not imports:
            return
        if any(_binds_urlparse_cached(node) for node in imports):
            self.fixable = True
            return
        end_line = imports[-1].end_lineno
        assert end_line is not None
        if end_line >= len(source.splitlines()):
            # No line to insert the import into.
            return
        pos = Pos(end_line + 1, 0)
        self.import_edit = Edit(start=pos, end=pos, replacement=_CACHED_URLPARSE_IMPORT)
        self.fixable = True

    def __call__(self, node: AST) -> Generator[Issue]:
        assert isinstance(node, Call)
        target = _get_urlparse_target(node)
        if target is None:
            return
        yield Issue(
            UNCACHED_URLPARSE,
            Pos.from_node(node),
            fix=self.build_fix(node, target),
        )

    def build_fix(self, node: Call, target: str) -> Fix | None:
        if not self.fixable:
            return None
        assert node.end_lineno is not None
        assert node.end_col_offset is not None
        edits = [
            Edit(
                start=Pos(node.lineno, node.col_offset),
                end=Pos(node.end_lineno, node.end_col_offset),
                replacement=f"urlparse_cached({target})",
            ),
        ]
        if self.import_edit is not None:
            edits.append(self.import_edit)
        return Fix(edits, message="use urlparse_cached()")


class OldSelectorIssueFinder:
    def __call__(self, node: AST) -> Generator[Issue]:
        if not (
            isinstance(node, Assign)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == "Selector"
        ):
            return

        # look for: Selector(response)
        if node.value.args:
            param = node.value.args[0]
            if self.is_response(param):
                yield Issue(IMPROPER_RESPONSE_SELECTOR, Pos.from_node(node))
                return

        # look for: Selector(response=response) or Selector(text=response.text)
        for kw in node.value.keywords:
            if self.has_response_for_keyword_parameter(kw):
                yield Issue(IMPROPER_RESPONSE_SELECTOR, Pos.from_node(node))
                return

    def is_response_dot_body_as_unicode(self, node):
        """Returns True if node represents response.body_as_unicode()"""
        return (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "response"
            and node.func.attr == "body_as_unicode"
        )

    def is_response_dot_text_or_body(self, node):
        """Return whether or not a node represents response.text or
        response.body
        """
        return (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == "response"
            and node.attr in ("text", "body")
        )

    def is_response(self, node):
        """Check if node represents an object named as response"""
        return isinstance(node, ast.Name) and node.id == "response"

    def has_response_for_keyword_parameter(self, node):
        """Check if response or response.text is passed as a keyword parameter
        as in: Selector(text=response.text) or Selector(response=response)
        """
        return (
            (node.arg == "text" and self.is_response_dot_text_or_body(node.value))
            or self.is_response_dot_body_as_unicode(node.value)
        ) or (node.arg == "response" and self.is_response(node.value))


def is_selector_call(node: AST) -> bool:
    """Return whether *node* is a call to a selector-returning method, e.g.
    ``response.css("a")``.
    """
    return (
        isinstance(node, Call)
        and isinstance(node.func, Attribute)
        and node.func.attr in ("css", "xpath")
    )


def is_first_index(node: Subscript) -> bool:
    return isinstance(node.slice, Constant) and node.slice.value == 0


def build_rename_fix(node: Attribute, name: str) -> Fix:
    """Build a fix that renames the attribute of *node* to *name*."""
    assert node.end_lineno is not None
    assert node.end_col_offset is not None
    edit = Edit(
        start=Pos(node.end_lineno, node.end_col_offset - len(node.attr)),
        end=Pos(node.end_lineno, node.end_col_offset),
        replacement=name,
    )
    return Fix([edit], message=f"replace {node.attr}() with {name}()")


def find_get_first_by_index_issues(node: AST) -> Generator[Issue]:
    assert isinstance(node, Call)
    node_func = node.func
    if not isinstance(node_func, Attribute) or node_func.attr not in ("extract", "get"):
        return

    # Selector getters take no arguments, so this is something else, e.g. an
    # lxml element, where get() reads an attribute.
    if node.args or node.keywords:
        return

    subscript_node = node_func.value
    if not isinstance(subscript_node, Subscript):
        return

    if not is_first_index(subscript_node):
        return

    if not is_selector_call(subscript_node.value):
        return

    yield Issue(IMPROPER_FIRST_MATCH_EXTRACTION, Pos.from_node(node))


class ExtractIssueFinder:
    """Finds calls to the old ``extract()`` and ``extract_first()`` getters.

    Handles both ``Subscript`` and ``Call`` nodes: ``extract()[0]`` is reported
    as a first match extraction issue, and the ``extract()`` call within it is
    not reported again as an old getter.
    """

    def __init__(self) -> None:
        self.indexed_extracts: set[int] = set()

    def __call__(self, node: AST) -> Generator[Issue]:
        if isinstance(node, Subscript):
            yield from self.find_extract_then_index_issues(node)
        else:
            assert isinstance(node, Call)
            yield from self.find_getter_issues(node)

    def find_extract_then_index_issues(self, node: Subscript) -> Generator[Issue]:
        if not is_first_index(node):
            return
        call = node.value
        if not (
            isinstance(call, Call)
            and isinstance(call.func, Attribute)
            and call.func.attr in ("extract", "getall")
            and is_selector_call(call.func.value)
        ):
            return
        self.indexed_extracts.add(id(call))
        yield Issue(IMPROPER_FIRST_MATCH_EXTRACTION, Pos.from_node(node))

    def find_getter_issues(self, node: Call) -> Generator[Issue]:
        func = node.func
        if not (isinstance(func, Attribute) and is_selector_call(func.value)):
            return
        if func.attr == "extract_first":
            yield Issue(
                IMPROPER_FIRST_MATCH_EXTRACTION,
                Pos.from_node(node),
                fix=build_rename_fix(func, "get"),
            )
        elif func.attr == "extract" and id(node) not in self.indexed_extracts:
            yield Issue(
                OLD_SELECTOR_GETTER,
                Pos.from_node(node),
                fix=build_rename_fix(func, "getall"),
            )


def find_absolute_nested_xpath_issues(node: AST) -> Generator[Issue]:
    assert isinstance(node, Call)
    func = node.func
    if not (isinstance(func, Attribute) and func.attr == "xpath" and node.args):
        return
    target = func.value
    if isinstance(target, Subscript):
        target = target.value
    if not is_selector_call(target):
        return
    expression = node.args[0]
    if not (
        isinstance(expression, Constant)
        and isinstance(expression.value, str)
        and expression.value.startswith("/")
    ):
        return
    yield Issue(ABSOLUTE_NESTED_XPATH, Pos.from_node(expression))
