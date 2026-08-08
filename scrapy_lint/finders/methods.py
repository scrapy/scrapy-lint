from __future__ import annotations

from ast import AsyncFunctionDef, ClassDef, FunctionDef
from typing import TYPE_CHECKING

from packaging.version import Version

from scrapy_lint.data.methods import DEPRECATED_ARGUMENTS
from scrapy_lint.issues import DEPRECATED_ARGUMENT, Issue, Pos

if TYPE_CHECKING:
    from ast import AST, arg, arguments
    from collections.abc import Generator

    from scrapy_lint.context import Context


def iter_required_args(args: arguments) -> Generator[arg]:
    positional = args.posonlyargs + args.args
    if args.defaults:
        positional = positional[: -len(args.defaults)]
    yield from positional
    for keyword, default in zip(args.kwonlyargs, args.kw_defaults, strict=True):
        if default is None:
            yield keyword


class DeprecatedArgumentIssueFinder:  # pylint: disable=too-few-public-methods
    def __init__(self, context: Context) -> None:
        self.project = context.project

    def __call__(self, node: AST) -> Generator[Issue]:
        assert isinstance(node, ClassDef)
        version = self.project.frozen_requirements.get("scrapy")
        if version is None:
            return
        for child in node.body:
            if not isinstance(child, (AsyncFunctionDef, FunctionDef)):
                continue
            deprecated_arguments = DEPRECATED_ARGUMENTS.get(child.name)
            if not deprecated_arguments:
                continue
            for argument in iter_required_args(child.args):
                versioning = deprecated_arguments.get(argument.arg)
                if versioning is None:
                    continue
                deprecated_in = versioning.deprecated_in
                assert isinstance(deprecated_in, Version)
                if version < deprecated_in:
                    continue
                yield Issue(
                    DEPRECATED_ARGUMENT,
                    Pos.from_node(argument),
                    f"deprecated in scrapy {deprecated_in}; "
                    f"{versioning.sunset_guidance}",
                )
