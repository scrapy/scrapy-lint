from __future__ import annotations

from ast import AST, Call, ClassDef, FunctionDef, expr, keyword
from typing import TYPE_CHECKING

from packaging.version import Version

from scrapy_lint.ast import definition_column, extract_literal_value, get_func_name
from scrapy_lint.data.apis import API_METHODS, API_PARAMETERS
from scrapy_lint.fixes import Fix, argument_removal_edit
from scrapy_lint.issues import DEPRECATED_API, DISCOURAGED_API, REMOVED_API, Issue, Pos
from scrapy_lint.versions import is_discouraged

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
        elif is_discouraged(api, version):
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
    def is_deprecated_value(api: API, node: expr) -> bool:
        value, is_literal = extract_literal_value(node)
        return api.deprecated_values is None or (
            is_literal and value in api.deprecated_values
        )

    def build_fix(self, api: API, kw: keyword) -> Fix:
        edit = argument_removal_edit(self.source, kw)
        return Fix([edit], message=f"remove the {api.name} argument")
