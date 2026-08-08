from __future__ import annotations

from ast import Assign, Constant, Dict, Expr, Import, ImportFrom, Name
from typing import TYPE_CHECKING

from scrapy_lint.data.addons import ADDONS
from scrapy_lint.fixes import Edit, Fix
from scrapy_lint.issues import Pos

if TYPE_CHECKING:
    from ast import Module, stmt

INDENT = "    "


class MissingAddonFixer:
    """Builder of fixes that enable add-ons in the ``ADDONS`` setting of a
    settings module.

    *source* is the source code of the settings module, and *module* its
    abstract syntax tree.
    """

    def __init__(self, source: str, module: Module):
        self.source = source
        self.imports: dict[str, str] = {}
        self.last_import: stmt | None = None
        self.docstring_end = 0
        self.assignment: Assign | None = None
        self.read(module)

    def read(self, module: Module) -> None:
        self.read_docstring(module)
        for node in module.body:
            if isinstance(node, (Import, ImportFrom)):
                self.read_import(node)
            elif isinstance(node, Assign) and any(
                isinstance(target, Name) and target.id == "ADDONS"
                for target in node.targets
            ):
                self.assignment = node

    def read_docstring(self, module: Module) -> None:
        if not module.body:
            return
        node = module.body[0]
        if (
            isinstance(node, Expr)
            and isinstance(node.value, Constant)
            and isinstance(node.value.value, str)
        ):
            assert node.end_lineno
            self.docstring_end = node.end_lineno

    def read_import(self, node: Import | ImportFrom) -> None:
        self.last_import = node
        if isinstance(node, ImportFrom) and not node.module:
            return
        for import_alias in node.names:
            name = import_alias.asname or import_alias.name
            self.imports[name] = (
                import_alias.name
                if isinstance(node, Import)
                else f"{node.module}.{import_alias.name}"
            )

    def build(self, paths: list[str], *, defined: bool) -> list[Fix | None]:
        """Return a fix for the first add-on import path in *paths*, which
        enables every add-on in *paths* at once, and ``None`` for the rest.

        *defined* tells whether the settings module assigns ``ADDONS``
        anywhere, including places where an add-on cannot be added, such as
        within a conditional block.
        """
        return [self.build_fix(paths, defined=defined), *[None] * (len(paths) - 1)]

    def build_fix(self, paths: list[str], *, defined: bool) -> Fix | None:
        entries = []
        modules = []
        for path in paths:
            reference, module = self.resolve(path)
            entries.append(f"{reference}: {ADDONS[path].priority}")
            if module:
                modules.append(module)
        if self.assignment is not None:
            edit = self.build_entry_edit(entries)
        elif defined:
            return None
        else:
            edit = self.build_setting_edit(entries)
        if edit is None:
            return None
        edits = [edit]
        if modules:
            edits.append(self.build_import_edit(modules))
        return Fix(edits, message="enable missing add-ons")

    def build_entry_edit(self, entries: list[str]) -> Edit | None:
        assert self.assignment
        value = self.assignment.value
        if not isinstance(value, Dict) or any(key is None for key in value.keys):
            return None
        if value.keys:
            last_key, last_value = value.keys[-1], value.values[-1]
            assert last_key
            assert last_value.end_lineno
            assert last_value.end_col_offset
            pos = Pos(last_value.end_lineno, last_value.end_col_offset)
            indent = " " * last_key.col_offset
            text = "".join(f",\n{indent}{entry}" for entry in entries)
        else:
            pos = Pos(value.lineno, value.col_offset + 1)
            indent = " " * self.assignment.col_offset + INDENT
            text = "".join(f"\n{indent}{entry}," for entry in entries) + "\n"
        return Edit(pos, pos, text)

    def build_setting_edit(self, entries: list[str]) -> Edit:
        body = "".join(f"{INDENT}{entry},\n" for entry in entries)
        separator = "\n" if self.source else ""
        pos = Pos(len(self.source.splitlines()) + 1, 0)
        return Edit(pos, pos, f"{separator}ADDONS = {{\n{body}}}\n")

    def build_import_edit(self, modules: list[str]) -> Edit:
        pos = Pos(self.import_line, 0)
        return Edit(pos, pos, "".join(f"import {module}\n" for module in modules))

    @property
    def import_line(self) -> int:
        """Line where an import statement can be added."""
        if self.last_import:
            assert self.last_import.end_lineno
            return self.last_import.end_lineno + 1
        return self.docstring_end + 1

    def resolve(self, path: str) -> tuple[str, str | None]:
        """Return the expression to use for the add-on at *path*, and the
        module to import for that expression to work, if any."""
        for name, imported in self.imports.items():
            if imported == path:
                return name, None
        module, _, attribute = path.rpartition(".")
        for name, imported in self.imports.items():
            if imported == module:
                return f"{name}.{attribute}", None
        return path, module
