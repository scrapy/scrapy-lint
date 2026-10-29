from __future__ import annotations

from ast import ImportFrom
from typing import TYPE_CHECKING

from scrapy_lint.ast import import_column, skip_spaces
from scrapy_lint.data.imports import IMPORTS
from scrapy_lint.fixes import Edit, Fix
from scrapy_lint.issues import DEPRECATED_IMPORT, REMOVED_IMPORT, Pos
from scrapy_lint.versions import check_sunset

if TYPE_CHECKING:
    from ast import AST
    from collections.abc import Generator

    from scrapy_lint.context import Project
    from scrapy_lint.imports import ImportedObject
    from scrapy_lint.issues import Issue


class ImportIssueFinder:
    def __init__(self, project: Project, source: str | None = None) -> None:
        self.project = project
        self.source = source

    def __call__(self, node) -> Generator[Issue]:
        if isinstance(node, ImportFrom) and node.level:
            return
        fix = self.build_fix(node)
        for import_alias in node.names:
            path = (
                f"{node.module}.{import_alias.name}"
                if isinstance(node, ImportFrom)
                else import_alias.name
            )
            imported_object = self.find(path)
            if (
                imported_object is None
                or imported_object.package not in self.project.version_ranges
            ):
                continue
            sunset = check_sunset(
                imported_object,
                self.project.version_ranges[imported_object.package],
                DEPRECATED_IMPORT,
                REMOVED_IMPORT,
            )
            if sunset is not None:
                yield sunset.issue(
                    Pos.from_node(node, import_column(import_alias)),
                    fix=fix,
                )

    def build_fix(self, node: AST) -> Fix | None:
        """Return a fix that points *node* at the module of the replacement of
        every name it imports, if they all have one and keep their name there."""
        if self.source is None or not isinstance(node, ImportFrom):
            return None
        module = None
        for import_alias in node.names:
            imported_object = self.find(f"{node.module}.{import_alias.name}")
            replacement = imported_object.replacement if imported_object else None
            if replacement is None:
                return None
            if module is None:
                module = replacement.rpartition(".")[0]
            if replacement != f"{module}.{import_alias.name}":
                return None
        assert module
        edit = module_edit(self.source, node, module)
        return None if edit is None else Fix([edit], f"import from {module} instead")

    @staticmethod
    def find(path: str) -> ImportedObject | None:
        """Return the entry for *path* or for the module that contains it."""
        parts = path.split(".")
        for length in range(len(parts), 0, -1):
            imported_object = IMPORTS.get(".".join(parts[:length]))
            if imported_object is not None:
                return imported_object
        return None


def module_edit(source: str, node: ImportFrom, module: str) -> Edit | None:
    """Return an edit that replaces the module of *node* with *module*."""
    assert node.module
    line = source.splitlines()[node.lineno - 1].encode()
    start = skip_spaces(line, node.col_offset + len("from"))
    end = start + len(node.module.encode())
    if line[start:end] != node.module.encode():
        return None
    return Edit(Pos(node.lineno, start), Pos(node.lineno, end), module)
