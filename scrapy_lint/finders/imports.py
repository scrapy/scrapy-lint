from __future__ import annotations

from ast import ImportFrom
from typing import TYPE_CHECKING

from scrapy_lint.ast import import_column
from scrapy_lint.data.imports import IMPORTS
from scrapy_lint.issues import DEPRECATED_IMPORT, REMOVED_IMPORT, Pos
from scrapy_lint.versions import check_sunset

if TYPE_CHECKING:
    from collections.abc import Generator

    from scrapy_lint.context import Project
    from scrapy_lint.imports import ImportedObject
    from scrapy_lint.issues import Issue


class ImportIssueFinder:
    def __init__(self, project: Project) -> None:
        self.project = project

    def __call__(self, node) -> Generator[Issue]:
        if isinstance(node, ImportFrom) and node.level:
            return
        for import_alias in node.names:
            path = (
                f"{node.module}.{import_alias.name}"
                if isinstance(node, ImportFrom)
                else import_alias.name
            )
            imported_object = self.find(path)
            if (
                imported_object is None
                or imported_object.package not in self.project.frozen_requirements
            ):
                continue
            yield from check_sunset(
                imported_object,
                self.project.frozen_requirements[imported_object.package],
                Pos.from_node(node, import_column(import_alias)),
                DEPRECATED_IMPORT,
                REMOVED_IMPORT,
            )

    @staticmethod
    def find(path: str) -> ImportedObject | None:
        """Return the entry for *path* or for the module that contains it."""
        parts = path.split(".")
        for length in range(len(parts), 0, -1):
            imported_object = IMPORTS.get(".".join(parts[:length]))
            if imported_object is not None:
                return imported_object
        return None
