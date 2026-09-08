from __future__ import annotations

from ast import AnnAssign, Assign, Attribute, ClassDef, Name
from typing import TYPE_CHECKING

from packaging.version import Version

from scrapy_lint.data.attributes import SPIDER_ATTRIBUTES
from scrapy_lint.issues import DEPRECATED_SPIDER_ATTRIBUTE, Issue, Pos

if TYPE_CHECKING:
    from ast import AST, stmt
    from collections.abc import Generator

    from scrapy_lint.context import Context


def is_spider(node: ClassDef) -> bool:
    for base in node.bases:
        name = base.attr if isinstance(base, Attribute) else getattr(base, "id", "")
        if name.endswith("Spider"):
            return True
    return False


def iter_assigned_names(node: stmt) -> Generator[Name]:
    if isinstance(node, AnnAssign):
        if isinstance(node.target, Name):
            yield node.target
    elif isinstance(node, Assign):
        for target in node.targets:
            if isinstance(target, Name):
                yield target


class SpiderAttributeIssueFinder:  # pylint: disable=too-few-public-methods
    def __init__(self, context: Context) -> None:
        self.project = context.project

    def __call__(self, node: AST) -> Generator[Issue]:
        assert isinstance(node, ClassDef)
        if not is_spider(node):
            return
        version = self.project.frozen_requirements.get("scrapy")
        if version is None:
            return
        for child in node.body:
            for target in iter_assigned_names(child):
                if target.id not in SPIDER_ATTRIBUTES:
                    continue
                versioning = SPIDER_ATTRIBUTES[target.id]
                deprecated_in = versioning.deprecated_in
                assert isinstance(deprecated_in, Version)
                if version < deprecated_in:
                    continue
                detail = f"deprecated in scrapy {deprecated_in}"
                if versioning.sunset_guidance:
                    detail += f"; {versioning.sunset_guidance}"
                yield Issue(
                    DEPRECATED_SPIDER_ATTRIBUTE,
                    Pos.from_node(target),
                    detail,
                )
