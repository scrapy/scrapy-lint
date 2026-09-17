from __future__ import annotations

from ast import AST, AsyncFunctionDef, Call, ClassDef, FunctionDef, expr, keyword
from typing import TYPE_CHECKING

from scrapy_lint.ast import definition_column, extract_literal_value, get_func_name
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


def implements(api: API, bases: set[str]) -> bool:
    """Return whether a class with the given *bases* is one that *api* applies
    to.

    An interface applies to every class that defines its methods. Otherwise
    the class must extend the class that defines *api*, which is matched by
    name suffix: subclasses keep the name of their base class as a suffix, both
    in Scrapy (e.g. CrawlSpider) and in Scrapy projects (e.g. BaseSpider), so
    a class of the project matches without resolving its own base classes.
    """
    return api.interface or any(base.endswith(api.local_name) for base in bases)


PARAMETERS = by_local_name(API_PARAMETERS)
METHODS = by_name(API_METHODS)
SPACES = (b" ", b"\t")


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

    def check_api(
        self,
        api: API,
        pos: Pos,
        subject: str,
        kw: keyword | None = None,
    ) -> Generator[Issue]:
        version = self.project.frozen_requirements.get(api.package)
        if version is None:
            return
        sunset = check_sunset(api, version, DEPRECATED_API, REMOVED_API)
        if sunset is None:
            return
        if (
            kw is not None
            and not sunset.removed
            and not self.is_deprecated_value(api, kw.value)
        ):
            return
        fix = self.build_fix(api, kw) if sunset.removed and kw else None
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


def keyword_removal_edit(source: str, kw: keyword) -> Edit:
    """Return an edit that removes the *kw* keyword argument from its call,
    together with the comma that separates it from a neighboring argument, and
    with the rest of its line where it has that line to itself."""
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


def skip_spaces(line: bytes, index: int) -> int:
    while line[index : index + 1] in SPACES:
        index += 1
    return index
