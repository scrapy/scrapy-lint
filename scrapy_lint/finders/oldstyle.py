import ast
from ast import AST, Assign, Attribute, Call, Constant, Subscript
from collections.abc import Generator

from scrapy_lint.fixes import Edit, Fix
from scrapy_lint.issues import (
    ABSOLUTE_NESTED_XPATH,
    IMPROPER_FIRST_MATCH_EXTRACTION,
    IMPROPER_RESPONSE_SELECTOR,
    IMPROPER_RESPONSE_URL_JOIN,
    OLD_SELECTOR_GETTER,
    Issue,
    Pos,
)


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
