from __future__ import annotations

from ast import (
    AST,
    AnnAssign,
    Assign,
    AsyncFunctionDef,
    Attribute,
    Call,
    ClassDef,
    Constant,
    Expr,
    For,
    FunctionDef,
    List,
    Name,
    Tuple,
    Yield,
    expr,
    get_source_segment,
    stmt,
)
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from scrapy_lint.fixes import Edit, Fix
from scrapy_lint.issues import UNNEEDED_START, Issue, Pos

if TYPE_CHECKING:
    from collections.abc import Generator

START_METHODS = frozenset({"start", "start_requests"})
LINE_LENGTH = 88


@dataclass
class StartUrls:
    """The :attr:`~scrapy.Spider.start_urls` equivalent of a start method."""

    urls: list[expr] = field(default_factory=list)
    #: Whether the method only re-sends the requests of ``start_urls``.
    reyields_start_urls: bool = False
    #: Whether every request sets ``dont_filter``, as ``start_urls`` does.
    dont_filter: bool = True


def is_self_attribute(node: expr, attr: str) -> bool:
    return (
        isinstance(node, Attribute)
        and node.attr == attr
        and isinstance(node.value, Name)
        and node.value.id == "self"
    )


def is_url_sequence(node: expr) -> bool:
    return isinstance(node, (List, Tuple)) and all(
        isinstance(elt, Constant) and isinstance(elt.value, str) for elt in node.elts
    )


def get_yielded_call(node: stmt) -> Call | None:
    if not isinstance(node, Expr) or not isinstance(node.value, Yield):
        return None
    call = node.value.value
    return call if isinstance(call, Call) else None


def get_request(node: stmt) -> tuple[expr, bool] | None:
    """Return the URL of a yielded request that ``start_urls`` could send, and
    whether it sets ``dont_filter``, or ``None`` for any other statement."""
    request = get_yielded_call(node)
    if request is None:
        return None
    func = request.func
    name = func.attr if isinstance(func, Attribute) else getattr(func, "id", None)
    if name != "Request" or len(request.args) > 1:
        return None
    url = request.args[0] if request.args else None
    dont_filter = False
    for keyword in request.keywords:
        if keyword.arg == "url":
            url = keyword.value
        elif keyword.arg == "callback":
            if not is_self_attribute(keyword.value, "parse"):
                return None
        elif keyword.arg == "dont_filter":
            if not isinstance(keyword.value, Constant):
                return None
            dont_filter = keyword.value.value is True
        else:
            return None
    return None if url is None else (url, dont_filter)


def get_loop_request(node: For) -> tuple[expr, bool] | None:
    if node.orelse or len(node.body) != 1 or not isinstance(node.target, Name):
        return None
    request = get_request(node.body[0])
    if request is None:
        return None
    url, dont_filter = request
    if not (isinstance(url, Name) and url.id == node.target.id):
        return None
    return node.iter, dont_filter


def get_start_urls(node: AsyncFunctionDef | FunctionDef) -> StartUrls | None:
    """Return what ``start_urls`` would have to be for the start method *node*
    to be unnecessary, or ``None`` if the method does more than ``start_urls``
    can."""
    body = node.body
    if isinstance(body[0], Expr) and isinstance(body[0].value, Constant):
        body = body[1:]
    if not body:
        return None
    result = StartUrls()
    for statement in body:
        if isinstance(statement, For):
            loop = get_loop_request(statement)
            if loop is None:
                return None
            urls, dont_filter = loop
            if is_self_attribute(urls, "start_urls"):
                result.reyields_start_urls = True
            elif is_url_sequence(urls):
                assert isinstance(urls, (List, Tuple))
                result.urls.extend(urls.elts)
            else:
                return None
        else:
            request = get_request(statement)
            if request is None:
                return None
            url, dont_filter = request
            if not (isinstance(url, Constant) and isinstance(url.value, str)):
                return None
            result.urls.append(url)
        result.dont_filter = result.dont_filter and dont_filter
    return result


class UnneededStartIssueFinder:
    def __init__(self, source: str | None = None):
        self.source = source

    def __call__(self, node: AST) -> Generator[Issue]:
        assert isinstance(node, ClassDef)
        for index, statement in enumerate(node.body):
            if not isinstance(statement, (AsyncFunctionDef, FunctionDef)):
                continue
            if statement.name not in START_METHODS or statement.decorator_list:
                continue
            start_urls = get_start_urls(statement)
            if start_urls is None:
                continue
            yield Issue(
                UNNEEDED_START,
                Pos.from_node(statement),
                fix=self.build_fix(node, index, start_urls),
            )

    def build_fix(
        self, node: ClassDef, index: int, start_urls: StartUrls
    ) -> Fix | None:
        """Build a fix that replaces the start method at *index* of the body of
        the spider class *node* with an equivalent ``start_urls``.

        Returns ``None`` (report only, no fix) when the rewrite would change
        duplicate filtering, when the URLs cannot be written as a literal list,
        or when there is no room for the rewrite in the class body.
        """
        if self.source is None or not start_urls.dont_filter:
            return None
        method = node.body[index]
        assert isinstance(method, (AsyncFunctionDef, FunctionDef))
        if start_urls.reyields_start_urls:
            if start_urls.urls or len(node.body) == 1:
                return None
            return self.build_removal(node, index)
        if any(self.assigns_start_urls(statement) for statement in node.body):
            return None
        replacement = self.build_start_urls(start_urls.urls, method.col_offset)
        if replacement is None:
            return None
        assert method.end_lineno is not None
        edit = Edit(
            start=Pos(method.lineno, 0),
            end=Pos(method.end_lineno + 1, 0),
            replacement=replacement,
        )
        return Fix([edit], message="replace the start method with start_urls")

    def build_removal(self, node: ClassDef, index: int) -> Fix:
        """Build a fix that removes the start method at *index* of the body of
        the spider class *node*, along with the blank lines that separate it
        from the rest of the class body."""
        assert self.source is not None
        method = node.body[index]
        assert method.end_lineno is not None
        lines = self.source.splitlines()
        first = 0 if index == 0 else node.body[index - 1].end_lineno
        assert first is not None
        start, end = method.lineno, method.end_lineno + 1
        while start - 1 > first and not lines[start - 2].strip():
            start -= 1
        while index == 0 and end <= len(lines) and not lines[end - 1].strip():
            end += 1
        edit = Edit(start=Pos(start, 0), end=Pos(end, 0), replacement="")
        return Fix([edit], message="remove the start method")

    def build_start_urls(self, urls: list[expr], indent: int) -> str | None:
        assert self.source is not None
        segments = []
        for url in urls:
            segment = get_source_segment(self.source, url)
            if not segment or segment[0] not in {'"', "'"} or segment[-1] != segment[0]:
                return None
            segments.append(segment)
        indentation = " " * indent
        line = f"{indentation}start_urls = [{', '.join(segments)}]"
        if len(line) <= LINE_LENGTH:
            return f"{line}\n"
        items = "".join(f"{indentation}    {segment},\n" for segment in segments)
        return f"{indentation}start_urls = [\n{items}{indentation}]\n"

    def assigns_start_urls(self, node: stmt) -> bool:
        return isinstance(node, (Assign, AnnAssign)) and any(
            isinstance(target, Name) and target.id == "start_urls"
            for target in (node.targets if isinstance(node, Assign) else [node.target])
        )
