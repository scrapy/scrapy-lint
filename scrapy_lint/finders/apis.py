from __future__ import annotations

from ast import AST, Call, ClassDef, FunctionDef, ImportFrom, expr, keyword
from typing import TYPE_CHECKING

from packaging.version import Version

from scrapy_lint.ast import (
    definition_column,
    extract_literal_value,
    get_func_name,
    import_column,
)
from scrapy_lint.data.apis import API_MEMBERS, API_METHODS, API_PARAMETERS
from scrapy_lint.fixes import Edit, Fix
from scrapy_lint.issues import DEPRECATED_API, DISCOURAGED_API, REMOVED_API, Issue, Pos
from scrapy_lint.versions import UnknownUnsupportedVersion

if TYPE_CHECKING:
    from collections.abc import Generator

    from scrapy_lint.apis import API
    from scrapy_lint.context import Context


def by_local_name(apis: tuple[API, ...]) -> dict[tuple[str, str], API]:
    """Map every API to the last component of its import path, which is how
    callables and classes are named at use sites, and its own name."""
    return {(api.path.rpartition(".")[2], api.name): api for api in apis}


PARAMETERS = by_local_name(API_PARAMETERS)
METHODS = by_local_name(API_METHODS)
MEMBERS = {(api.path, api.name): api for api in API_MEMBERS}
SPACES = (b" ", b"\t")


class APIIssueFinder:
    def __init__(self, context: Context, source: str | None = None):
        self.project = context.project
        self.source = source

    def __call__(self, node: AST) -> Generator[Issue]:
        if isinstance(node, Call):
            yield from self.check_call(node)
        elif isinstance(node, ClassDef):
            yield from self.check_class(node)
        else:
            assert isinstance(node, ImportFrom)
            yield from self.check_import(node)

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
        for statement in node.body:
            if not isinstance(statement, FunctionDef):
                continue
            for base in bases:
                api = METHODS.get((base, statement.name))
                if api is None:
                    continue
                pos = Pos(statement.lineno, definition_column(statement))
                subject = f"{api.name} method of {api.path}"
                yield from self.check_api(api, pos, subject)

    def check_import(self, node: ImportFrom) -> Generator[Issue]:
        for imported in node.names:
            api = MEMBERS.get((node.module or "", imported.name))
            if api is not None:
                pos = Pos(node.lineno, import_column(imported))
                yield from self.check_api(api, pos, f"{api.path}.{api.name}")

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
        versioning = api.versioning
        deprecated_in = versioning.deprecated_in
        assert isinstance(deprecated_in, Version)
        sunset = f"{api.package} {deprecated_in}"
        if versioning.removed_in and version >= versioning.removed_in:
            detail = (
                f"{subject}, deprecated in {sunset}, removed in {versioning.removed_in}"
            )
            fix = self.build_fix(api, kw) if kw else None
            yield Issue(REMOVED_API, pos, detail, fix=fix)
            return
        if kw is not None and not self.is_deprecated_value(api, kw.value):
            return
        if version >= deprecated_in:
            yield Issue(
                DEPRECATED_API,
                pos,
                self.detail(api, f"{subject}, deprecated in {sunset}"),
            )
        elif self.is_discouraged(api, version):
            yield Issue(
                DISCOURAGED_API,
                pos,
                self.detail(api, f"{subject}, to be deprecated in {sunset}"),
            )

    @staticmethod
    def detail(api: API, detail: str) -> str:
        if api.versioning.sunset_guidance:
            detail += f"; {api.versioning.sunset_guidance}"
        return detail

    @staticmethod
    def is_discouraged(api: API, version: Version) -> bool:
        discouraged_in = api.discouraged_in
        return discouraged_in is not None and (
            isinstance(discouraged_in, UnknownUnsupportedVersion)
            or version >= discouraged_in
        )

    @staticmethod
    def is_deprecated_value(api: API, node: expr) -> bool:
        value, is_literal = extract_literal_value(node)
        return api.deprecated_values is None or (
            is_literal and value in api.deprecated_values
        )

    def build_fix(self, api: API, kw: keyword) -> Fix | None:
        if not api.droppable or self.source is None:
            return None
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
