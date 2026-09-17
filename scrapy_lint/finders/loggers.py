from __future__ import annotations

from ast import (
    AST,
    Assign,
    AsyncFunctionDef,
    Attribute,
    Call,
    ClassDef,
    Constant,
    Dict,
    FunctionDef,
    Name,
    expr,
    walk,
)
from typing import TYPE_CHECKING

from scrapy_lint.fixes import Edit, Fix
from scrapy_lint.issues import NON_SPIDER_LOGGER, Issue, Pos

if TYPE_CHECKING:
    from collections.abc import Generator

LOG_METHODS = frozenset(
    {
        "critical",
        "debug",
        "error",
        "exception",
        "fatal",
        "info",
        "log",
        "warn",
        "warning",
    },
)


def name(node: expr) -> str | None:
    """Return the last component of a dotted name, e.g. ``Spider`` for
    ``scrapy.Spider``."""
    if isinstance(node, Name):
        return node.id
    if isinstance(node, Attribute):
        return node.attr
    return None


def is_spider_class(node: ClassDef) -> bool:
    return any((name(base) or "").endswith("Spider") for base in node.bases)


def is_get_logger(node: expr) -> bool:
    return isinstance(node, Call) and name(node.func) == "getLogger"


def iter_methods(node: ClassDef) -> Generator[FunctionDef | AsyncFunctionDef]:
    for child in node.body:
        if (
            isinstance(child, (FunctionDef, AsyncFunctionDef))
            and child.args.args
            and child.args.args[0].arg == "self"
        ):
            yield child


def has_spider_extra(node: Call) -> bool:
    """Return whether the call already binds the log record to a spider through
    its ``extra`` dictionary."""
    for keyword in node.keywords:
        if keyword.arg != "extra":
            continue
        if not isinstance(keyword.value, Dict):
            return True
        return any(
            isinstance(key, Constant) and key.value == "spider"
            for key in keyword.value.keys
        )
    return False


def build_fix(node: Name) -> Fix:
    assert node.end_lineno is not None
    assert node.end_col_offset is not None
    edit = Edit(
        start=Pos(node.lineno, node.col_offset),
        end=Pos(node.end_lineno, node.end_col_offset),
        replacement="self.logger",
    )
    return Fix([edit], message="use self.logger")


class SpiderLoggerIssueFinder:
    def __init__(self):
        self.loggers: set[str] = set()

    def __call__(self, node: AST) -> Generator[Issue]:
        if isinstance(node, Assign):
            self.track_logger(node)
            return
        assert isinstance(node, ClassDef)
        if not is_spider_class(node):
            return
        for method in iter_methods(node):
            for child in walk(method):
                if isinstance(child, Call):
                    yield from self.check_call(child)

    def track_logger(self, node: Assign) -> None:
        if not is_get_logger(node.value):
            return
        for target in node.targets:
            if isinstance(target, Name):
                self.loggers.add(target.id)

    def check_call(self, node: Call) -> Generator[Issue]:
        if not isinstance(node.func, Attribute) or node.func.attr not in LOG_METHODS:
            return
        logger = node.func.value
        if not isinstance(logger, Name):
            return
        if logger.id != "logging" and logger.id not in self.loggers:
            return
        if has_spider_extra(node):
            return
        yield Issue(NON_SPIDER_LOGGER, Pos.from_node(logger), fix=build_fix(logger))
