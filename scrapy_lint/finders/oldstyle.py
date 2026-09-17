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
    IMPROPER_FIRST_MATCH_EXTRACTION,
    IMPROPER_RESPONSE_SELECTOR,
    IMPROPER_RESPONSE_URL_JOIN,
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


def find_get_first_by_index_issues(node: AST) -> Generator[Issue]:
    assert isinstance(node, Call)
    node_func = node.func
    if not isinstance(node_func, Attribute) or node_func.attr not in ("extract", "get"):
        return

    subscript_node = node_func.value
    if not isinstance(subscript_node, Subscript):
        return

    if not isinstance(subscript_node.slice, Constant):
        return

    index = subscript_node.slice.value
    if index != 0:
        return

    subscripted_value = subscript_node.value
    if not isinstance(subscripted_value, Call):
        return

    subscripted_value_func = subscripted_value.func
    if not (
        isinstance(subscripted_value_func, Attribute)
        and subscripted_value_func.attr in ("css", "xpath")
    ):
        return

    yield Issue(IMPROPER_FIRST_MATCH_EXTRACTION, Pos.from_node(node))


def find_extract_then_index_issues(node: AST) -> Generator[Issue]:
    assert isinstance(node, Subscript)
    if not isinstance(node.slice, Constant):
        return
    if node.slice.value != 0:
        return
    if not isinstance(node.value, Call):
        return
    if not (
        isinstance(node.value.func, Attribute)
        and node.value.func.attr in ("extract", "getall")
    ):
        return
    extract_target = node.value.func.value
    if not (
        isinstance(extract_target, Call)
        and isinstance(extract_target.func, Attribute)
        and extract_target.func.attr in ("css", "xpath")
    ):
        return
    yield Issue(IMPROPER_FIRST_MATCH_EXTRACTION, Pos.from_node(node))
