from __future__ import annotations

from ast import (
    AST,
    AsyncFunctionDef,
    Attribute,
    Call,
    ClassDef,
    Constant,
    FunctionDef,
    Name,
    Starred,
    expr,
    keyword,
    walk,
)
from logging import getLevelName
from typing import TYPE_CHECKING

from scrapy_lint.ast import (
    definition_column,
    extract_literal_value,
    get_func_name,
    skip_spaces,
)
from scrapy_lint.data.apis import API_METHODS, API_PARAMETERS
from scrapy_lint.fixes import Edit, Fix
from scrapy_lint.issues import DEPRECATED_API, REMOVED_API, Pos
from scrapy_lint.versions import check_sunset

if TYPE_CHECKING:
    from collections.abc import Generator

    from scrapy_lint.apis import API
    from scrapy_lint.context import Context
    from scrapy_lint.issues import Issue


def by_local_name(apis: tuple[API, ...]) -> dict[tuple[str, str], API]:
    """Map every API to the name of its callable and its own name."""
    return {(api.local_name, api.name): api for api in apis}


def by_name(apis: tuple[API, ...]) -> dict[str, list[API]]:
    """Map every API to its own name, the class it belongs to being matched
    separately."""
    result: dict[str, list[API]] = {}
    for api in apis:
        result.setdefault(api.name, []).append(api)
    return result


def extends(api: API, bases: set[str]) -> bool:
    """Return whether a class with the given *bases* extends the class that
    defines *api*, which is matched by name suffix: subclasses keep the name of
    their base class as a suffix, both in Scrapy (e.g. CrawlSpider) and in
    Scrapy projects (e.g. BaseSpider), so a class of the project matches
    without resolving its own base classes."""
    return any(base.endswith(api.local_name) for base in bases)


def implements(api: API, bases: set[str]) -> bool:
    """Return whether a class with the given *bases* is one that *api* applies
    to: an interface applies to every class that defines its methods, any other
    API to the classes that extend the class that defines it."""
    return api.interface or extends(api, bases)


def iter_self_calls(node: ClassDef) -> Generator[tuple[Call, str]]:
    """Yield every call on ``self`` within *node*, with the name of the method
    it calls."""
    for child in walk(node):
        if (
            isinstance(child, Call)
            and isinstance(child.func, Attribute)
            and isinstance(child.func.value, Name)
            and child.func.value.id == "self"
        ):
            yield child, child.func.attr


def level_method(node: expr | None) -> str | None:
    """Return the ``Spider.logger`` method for the logging level *node*, or
    ``None`` where it is not one of the standard levels."""
    if node is None:
        return "debug"
    if isinstance(node, Constant):
        name = getLevelName(node.value) if isinstance(node.value, int) else None
    else:
        name = get_func_name(node)
    return LEVEL_METHODS.get(name) if isinstance(name, str) else None


def spider_log_fix(source: str, node: Call) -> Fix | None:
    """Return a fix that turns the ``Spider.log()`` call *node* into a call of
    the ``Spider.logger`` method for its level, or ``None`` where the level is
    not a standard one or the arguments cannot be told apart."""
    args = node.args
    if not args or any(isinstance(arg, Starred) for arg in args):
        return None
    _, *rest = args
    if len(rest) > 1:
        return None
    level: expr | keyword | None = (
        rest[0]
        if rest
        else next((kw for kw in node.keywords if kw.arg == "level"), None)
    )
    method = level_method(level.value if isinstance(level, keyword) else level)
    if method is None:
        return None
    func = node.func
    assert func.end_lineno is not None
    assert func.end_col_offset is not None
    end = Pos(func.end_lineno, func.end_col_offset)
    edits = [Edit(Pos.from_node(func), end, f"self.logger.{method}")]
    if level is not None:
        edits.append(keyword_removal_edit(source, level))
    return Fix(edits, message=f"replace with self.logger.{method}()")


PARAMETERS = by_local_name(API_PARAMETERS)
METHODS = by_name(API_METHODS)
CLASS_METHODS = by_local_name(API_METHODS)
CALL_FIXES = {("scrapy.Spider", "log"): spider_log_fix}
LEVEL_METHODS = {
    "DEBUG": "debug",
    "INFO": "info",
    "WARN": "warning",
    "WARNING": "warning",
    "ERROR": "error",
    "FATAL": "critical",
    "CRITICAL": "critical",
}


class APIIssueFinder:
    def __init__(self, context: Context, source: str):
        self.project = context.project
        self.source = source

    def __call__(self, node: AST) -> Generator[Issue]:
        if isinstance(node, Call):
            yield from self.check_call(node)
        else:
            assert isinstance(node, ClassDef)
            yield from self.check_class(node)

    def check_call(self, node: Call) -> Generator[Issue]:
        name = get_func_name(node.func)
        if name is None:
            return
        if isinstance(node.func, Attribute):
            receiver = get_func_name(node.func.value)
            api = CLASS_METHODS.get((receiver, name)) if receiver else None
            if api is not None:
                subject = f"{api.name} method of {api.path}"
                yield from self.check_api(api, Pos.from_node(node), subject)
        for kw in node.keywords:
            if kw.arg is None:
                continue
            api = PARAMETERS.get((name, kw.arg))
            if api is not None:
                pos = Pos(kw.lineno, kw.col_offset)
                subject = f"{api.name} parameter of {api.path}"
                yield from self.check_api(api, pos, subject, kw=kw)

    def check_class(self, node: ClassDef) -> Generator[Issue]:
        bases = {name for base in node.bases if (name := get_func_name(base))}
        methods = {
            statement.name
            for statement in node.body
            if isinstance(statement, (AsyncFunctionDef, FunctionDef))
        }
        for statement in node.body:
            if not isinstance(statement, FunctionDef):
                continue
            for api in METHODS.get(statement.name, ()):
                if not implements(api, bases) or api.paired_with in methods:
                    continue
                pos = Pos(statement.lineno, definition_column(statement))
                subject = f"{api.name} method of {api.path}"
                yield from self.check_api(api, pos, subject)
        for call, name in iter_self_calls(node):
            for api in METHODS.get(name, ()):
                if not extends(api, bases):
                    continue
                subject = f"{api.name} method of {api.path}"
                build_fix = CALL_FIXES.get((api.path, api.name))
                fix = build_fix(self.source, call) if build_fix else None
                yield from self.check_api(api, Pos.from_node(call), subject, fix=fix)

    def check_api(
        self,
        api: API,
        pos: Pos,
        subject: str,
        kw: keyword | None = None,
        fix: Fix | None = None,
    ) -> Generator[Issue]:
        versions = self.project.version_ranges.get(api.package)
        if versions is None:
            return
        sunset = check_sunset(api, versions, DEPRECATED_API, REMOVED_API)
        if sunset is None:
            return
        if (
            kw is not None
            and not sunset.removed
            and not self.is_deprecated_value(api, kw.value)
        ):
            return
        if kw is not None and sunset.removed:
            fix = self.build_fix(api, kw)
        yield sunset.issue(pos, subject=subject, fix=fix)

    @staticmethod
    def is_deprecated_value(api: API, node: expr) -> bool:
        value, is_literal = extract_literal_value(node)
        return api.deprecated_values is None or (
            is_literal and value in api.deprecated_values
        )

    def build_fix(self, api: API, kw: keyword) -> Fix:
        edit = keyword_removal_edit(self.source, kw)
        return Fix([edit], message=f"remove the {api.name} argument")


def keyword_removal_edit(source: str, kw: keyword | expr) -> Edit:
    """Return an edit that removes the *kw* argument from its call, together
    with the comma that separates it from a neighboring argument, and with the
    rest of its line where it has that line to itself."""
    assert kw.end_lineno is not None
    assert kw.end_col_offset is not None
    lines = source.splitlines()
    start = Pos(kw.lineno, kw.col_offset)
    end = Pos(kw.end_lineno, kw.end_col_offset)
    before = lines[start.line - 1].encode()[: start.column]
    line = lines[end.line - 1].encode()
    index = skip_spaces(line, end.column)
    stripped_before = before.rstrip(b" \t")
    if line[index : index + 1] == b",":
        end = Pos(end.line, skip_spaces(line, index + 1))
    elif stripped_before.endswith(b","):
        start = Pos(start.line, len(stripped_before) - 1)
    if not before.strip() and not line[end.column :].strip():
        return Edit(Pos(start.line, 0), Pos(end.line + 1, 0), "")
    return Edit(start, end, "")
