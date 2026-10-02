from __future__ import annotations

from ast import AsyncFunctionDef, ClassDef, FunctionDef, Name, walk
from typing import TYPE_CHECKING

from packaging.version import Version

from scrapy_lint.data.methods import DEPRECATED_ARGUMENTS
from scrapy_lint.fixes import Fix, argument_removal_edit
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


class DeprecatedArgumentIssueFinder:
    def __init__(self, context: Context, source: str | None = None) -> None:
        self.project = context.project
        self.source = source

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
                    fix=self.build_fix(child, argument),
                )

    def build_fix(
        self,
        method: AsyncFunctionDef | FunctionDef,
        argument: arg,
    ) -> Fix | None:
        """Build a fix that drops *argument* from the signature of *method*.

        Returns ``None`` (report only, no fix) when the method uses the name of
        the argument, or when dropping it would leave a ``/`` or ``*`` marker
        with nothing on the side that needs one.
        """
        if self.source is None:
            return None
        args = method.args
        if args.posonlyargs == [argument] or (
            not args.vararg and args.kwonlyargs == [argument]
        ):
            return None
        if any(
            isinstance(node, Name) and node.id == argument.arg for node in walk(method)
        ):
            return None
        edit = argument_removal_edit(self.source, argument)
        return Fix([edit], message=f"remove the {argument.arg} argument")
