from __future__ import annotations

from ast import (
    AsyncFunctionDef,
    Attribute,
    ClassDef,
    FunctionDef,
    If,
    Import,
    ImportFrom,
    Module,
    Name,
    expr,
    walk,
)
from typing import TYPE_CHECKING

from scrapy_lint.issues import HIDDEN_CALLBACK_TYPE_HINT, Issue, Pos

if TYPE_CHECKING:
    from collections.abc import Generator

    from scrapy_lint.context import Project

#: Package that makes Scrapy resolve callback annotations at run time.
INJECTION_PACKAGE = "scrapy-poet"


def has_future_annotations(tree: Module) -> bool:
    return any(
        isinstance(node, ImportFrom)
        and node.module == "__future__"
        and any(alias.name == "annotations" for alias in node.names)
        for node in tree.body
    )


def is_type_checking(test: expr) -> bool:
    return (isinstance(test, Name) and test.id == "TYPE_CHECKING") or (
        isinstance(test, Attribute) and test.attr == "TYPE_CHECKING"
    )


def iter_type_checking_names(tree: Module) -> Generator[str]:
    """Yield the names that *tree* only imports for type checking."""
    for node in tree.body:
        if not isinstance(node, If) or not is_type_checking(node.test):
            continue
        for child in node.body:
            for subnode in walk(child):
                if not isinstance(subnode, (Import, ImportFrom)):
                    continue
                for alias in subnode.names:
                    yield alias.asname or alias.name.split(".")[0]


def is_spider(node: ClassDef) -> bool:
    return any(
        (isinstance(base, Name) and base.id.endswith("Spider"))
        or (isinstance(base, Attribute) and base.attr.endswith("Spider"))
        for base in node.bases
    )


def iter_annotations(node: FunctionDef | AsyncFunctionDef) -> Generator[expr]:
    args = node.args
    for arg in (
        *args.posonlyargs,
        *args.args,
        *args.kwonlyargs,
        args.vararg,
        args.kwarg,
    ):
        if arg is not None and arg.annotation is not None:
            yield arg.annotation
    if node.returns is not None:
        yield node.returns


class HiddenTypeHintIssueFinder:
    def __init__(self, project: Project) -> None:
        self.project = project

    def check(self, tree: Module) -> Generator[Issue]:
        # ponytail: Python 3.14 evaluates annotations lazily even without the
        # future import, but the target Python version is unknown here.
        if INJECTION_PACKAGE not in self.project.packages or not has_future_annotations(
            tree,
        ):
            return
        hidden = set(iter_type_checking_names(tree))
        if not hidden:
            return
        for node in walk(tree):
            if not isinstance(node, ClassDef) or not is_spider(node):
                continue
            for method in node.body:
                if not isinstance(method, (FunctionDef, AsyncFunctionDef)):
                    continue
                yield from self.check_method(method, hidden)

    def check_method(
        self,
        node: FunctionDef | AsyncFunctionDef,
        hidden: set[str],
    ) -> Generator[Issue]:
        for annotation in iter_annotations(node):
            for subnode in walk(annotation):
                if isinstance(subnode, Name) and subnode.id in hidden:
                    yield Issue(
                        HIDDEN_CALLBACK_TYPE_HINT,
                        Pos.from_node(subnode),
                        detail=subnode.id,
                    )
