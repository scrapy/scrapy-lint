from __future__ import annotations

from ast import (
    AST,
    AnnAssign,
    Attribute,
    Call,
    ClassDef,
    Import,
    ImportFrom,
    Module,
    Name,
    Subscript,
    expr,
)
from typing import TYPE_CHECKING

from scrapy_lint.ast import definition_column
from scrapy_lint.fixes import Edit, Fix
from scrapy_lint.issues import NO_ATTRS_DEFINE, Issue, Pos

if TYPE_CHECKING:
    from collections.abc import Generator

PAGE_MODULE = "web_poet"
PAGE_BASES = frozenset({"Injectable", "ItemPage", "WebPage"})

# Decorators that turn class annotations into instance fields, matched by their
# last component, so that both attrs APIs (attrs.define, attr.s) and dataclasses
# are covered.
FIELD_DECORATORS = frozenset(
    {"attributes", "attrs", "dataclass", "define", "frozen", "mutable", "s"},
)


def dotted_name(node: expr) -> str | None:
    """Return the dotted name that *node* spells out, e.g. ``web_poet.WebPage``.

    Returns ``None`` for expressions that are not a name or an attribute chain
    rooted at one.
    """
    parts = []
    while isinstance(node, Attribute):
        parts.append(node.attr)
        node = node.value
    if not isinstance(node, Name):
        return None
    parts.append(node.id)
    return ".".join(reversed(parts))


def unsubscript(node: expr) -> expr:
    return node.value if isinstance(node, Subscript) else node


def last_component(node: expr) -> str | None:
    name = dotted_name(node)
    return None if name is None else name.rpartition(".")[2]


def is_class_var(annotation: expr) -> bool:
    return last_component(unsubscript(annotation)) == "ClassVar"


class NoAttrsDefineIssueFinder:
    """Report page objects that declare attributes without an attrs decorator.

    Base classes are resolved through the imports of the module being linted,
    so only page objects that subclass a :doc:`web-poet <web-poet:index>` class
    directly are covered.
    """

    def __init__(self, source: str):
        self.source = source
        # Name as used in the module, e.g. WebPage, mapped to the dotted path it
        # was imported from, e.g. web_poet.WebPage.
        self.imports: dict[str, str] = {}
        self.import_pos = Pos()
        self.attrs_imported = False
        self.import_fixed = False

    def __call__(self, node: AST) -> Generator[Issue]:
        if isinstance(node, Module):
            self.scan_imports(node)
            return
        assert isinstance(node, ClassDef)
        if not any(self.is_page_base(base) for base in node.bases):
            return
        if any(self.defines_fields(decorator) for decorator in node.decorator_list):
            return
        if not any(
            isinstance(stmt, AnnAssign) and not is_class_var(stmt.annotation)
            for stmt in node.body
        ):
            return
        yield Issue(
            NO_ATTRS_DEFINE,
            Pos(node.lineno, definition_column(node)),
            fix=self.build_fix(node),
        )

    def scan_imports(self, module: Module) -> None:
        """Index the module-level imports, and remember where a new import can
        be inserted.
        """
        found_import_pos = False
        for stmt in module.body:
            if isinstance(stmt, Import):
                for alias in stmt.names:
                    root = alias.name.partition(".")[0]
                    self.imports[alias.asname or root] = (
                        alias.name if alias.asname else root
                    )
            elif isinstance(stmt, ImportFrom):
                if stmt.module and not stmt.level:
                    for alias in stmt.names:
                        self.imports[alias.asname or alias.name] = (
                            f"{stmt.module}.{alias.name}"
                        )
                # An import cannot be inserted before a __future__ one.
                if stmt.module == "__future__":
                    continue
            else:
                continue
            if not found_import_pos:
                self.import_pos = Pos(stmt.lineno, stmt.col_offset)
                found_import_pos = True
        self.attrs_imported = self.imports.get("attrs") == "attrs"

    def resolve(self, node: expr) -> str | None:
        name = dotted_name(node)
        if name is None:
            return None
        root, _, rest = name.partition(".")
        target = self.imports.get(root)
        if target is None:
            return None
        return f"{target}.{rest}" if rest else target

    def is_page_base(self, base: expr) -> bool:
        path = self.resolve(unsubscript(base))
        if path is None:
            return False
        module, _, name = path.rpartition(".")
        return name in PAGE_BASES and module.partition(".")[0] == PAGE_MODULE

    def defines_fields(self, decorator: expr) -> bool:
        if isinstance(decorator, Call):
            decorator = decorator.func
        return last_component(decorator) in FIELD_DECORATORS

    def build_fix(self, node: ClassDef) -> Fix:
        indent = self.source.splitlines()[node.lineno - 1][: node.col_offset]
        pos = Pos(node.lineno, node.col_offset)
        edits = [Edit(start=pos, end=pos, replacement=f"@attrs.define\n{indent}")]
        if not self.attrs_imported and not self.import_fixed:
            edits.append(
                Edit(
                    start=self.import_pos,
                    end=self.import_pos,
                    replacement="import attrs\n",
                ),
            )
            self.import_fixed = True
        return Fix(edits, message="add an @attrs.define decorator")
