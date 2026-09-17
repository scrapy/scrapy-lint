from __future__ import annotations

from ast import AST, Attribute, ImportFrom
from typing import TYPE_CHECKING

from scrapy_lint.ast import import_column, import_path_from_attribute
from scrapy_lint.data.injectables import INJECTABLES
from scrapy_lint.issues import UNSUPPORTED_INJECTABLE, Issue, Pos

if TYPE_CHECKING:
    from collections.abc import Generator

    from scrapy_lint.context import Context

INJECTABLE_MODULE = "web_poet"


class InjectableIssueFinder:  # pylint: disable=too-few-public-methods
    def __init__(self, context: Context) -> None:
        self.project = context.project

    def __call__(self, node: AST) -> Generator[Issue]:
        if isinstance(node, ImportFrom):
            if node.module != INJECTABLE_MODULE and not (node.module or "").startswith(
                f"{INJECTABLE_MODULE}."
            ):
                return
            for alias_ in node.names:
                pos = Pos(alias_.lineno, import_column(alias_))
                yield from self._check(alias_.name, pos)
        elif isinstance(node, Attribute):
            path = import_path_from_attribute(node)
            if len(path) > 1 and path[0] == INJECTABLE_MODULE:
                yield from self._check(path[-1], Pos.from_node(node))

    def _check(self, name: str, pos: Pos) -> Generator[Issue]:
        if name not in INJECTABLES:
            return
        package, added_in = INJECTABLES[name]
        version = self.project.frozen_requirements.get(package)
        if version is not None and version < added_in:
            yield Issue(UNSUPPORTED_INJECTABLE, pos, f"added in {package} {added_in}")
