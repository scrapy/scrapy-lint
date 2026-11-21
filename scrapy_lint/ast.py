from __future__ import annotations

from ast import (
    AsyncFunctionDef,
    Attribute,
    Call,
    ClassDef,
    Constant,
    Dict,
    FunctionDef,
    Import,
    ImportFrom,
    List,
    Module,
    Name,
    alias,
    expr,
    walk,
)
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Generator

SPACES = (b" ", b"\t")


def extract_literal_value(node) -> tuple[Any, bool]:
    """Extract a literal value from an AST node.

    Returns:
        tuple: (value, is_literal) where is_literal indicates if the node
        represents a literal value that can be compared.
    """
    if isinstance(node, Constant):
        return node.value, True
    if isinstance(node, List):
        # Only extract if all elements are literals
        elements = []
        for elt in node.elts:
            value, is_literal = extract_literal_value(elt)
            if not is_literal:
                return None, False  # Contains non-literal
            elements.append(value)
        return elements, True
    if isinstance(node, Dict):
        result = {}
        for key_node, value_node in zip(node.keys, node.values, strict=False):
            key, key_is_literal = extract_literal_value(key_node)
            value, value_is_literal = extract_literal_value(value_node)
            if not key_is_literal or not value_is_literal:
                return None, False  # Contains non-literal
            result[key] = value
        return result, True
    return None, False  # Not a literal


def get_func_name(f: expr) -> str | None:
    if hasattr(f, "attr"):
        return f.attr
    if hasattr(f, "id"):
        return f.id
    return None


def is_dict(node: expr) -> bool:
    return isinstance(node, Dict) or (
        isinstance(node, Call)
        and isinstance(node.func, Name)
        and node.func.id == "dict"
    )


def iter_dict(node: Dict | Call) -> Generator[tuple[expr, expr]]:
    if isinstance(node, Dict):
        yield from zip(node.keys, node.values, strict=False)
    elif (
        isinstance(node, Call)
        and isinstance(node.func, Name)
        and node.func.id == "dict"
    ):
        for kw in node.keywords:
            yield (
                Constant(value=kw.arg, col_offset=kw.col_offset, lineno=kw.lineno),
                kw.value,
            )


def definition_column(node: ClassDef | FunctionDef) -> int:
    offset = len("class ") if isinstance(node, ClassDef) else len("def ")
    return node.col_offset + offset


def import_column(alias_: alias) -> int:
    if alias_.asname:
        # For "from foo import BAR as BAZ" or "import foo as BAR", point to "BAZ"/"BAR"
        # Need to find position of alias name after " as "
        return alias_.col_offset + len(alias_.name) + 4  # " as " is 4 chars
    # For "from foo import FOO" or "import FOO", point to "FOO"
    return alias_.col_offset


@dataclass
class ModuleIndex:
    """Module-wide data that node-level finders cannot get from their node."""

    functions: dict[str, FunctionDef | AsyncFunctionDef] = field(default_factory=dict)
    """Function definitions by name, class scopes flattened."""

    imports: dict[str, str] = field(default_factory=dict)
    """Import paths by the local name they are bound to."""

    @classmethod
    def from_tree(cls, tree: Module) -> ModuleIndex:
        index = cls()
        for node in walk(tree):
            if isinstance(node, (AsyncFunctionDef, FunctionDef)):
                index.functions.setdefault(node.name, node)
            elif isinstance(node, ImportFrom):
                if node.module and not node.level:
                    for alias_ in node.names:
                        name = alias_.asname or alias_.name
                        index.imports[name] = f"{node.module}.{alias_.name}"
            elif isinstance(node, Import):
                for alias_ in node.names:
                    name = alias_.asname or alias_.name.split(".")[0]
                    index.imports[name] = alias_.name
        return index

    def package(self, node: expr) -> str | None:
        """Return the package *node*, a reference to an imported name, comes from."""
        while isinstance(node, Attribute):
            node = node.value
        if not isinstance(node, Name):
            return None
        path = self.imports.get(node.id)
        return path.split(".")[0] if path else None


def skip_spaces(line: bytes, index: int) -> int:
    """Return the index of the first non-space byte of *line* at or after
    *index*."""
    while line[index : index + 1] in SPACES:
        index += 1
    return index
