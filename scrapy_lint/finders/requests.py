from __future__ import annotations

from ast import AST, Attribute, Call, Constant, Dict, Name, Subscript, Tuple, arg, expr
from typing import TYPE_CHECKING

from scrapy_lint.ast import get_func_name, is_dict, iter_dict
from scrapy_lint.issues import (
    MISSING_PROVIDER_PARAMS,
    UNSAFE_META_COPY,
    UNUSED_AUTOMAP_PARAMS,
    ZYTE_RAW_PARAMS,
    Issue,
    Pos,
)

if TYPE_CHECKING:
    from ast import AsyncFunctionDef, FunctionDef
    from collections.abc import Generator

    from scrapy_lint.ast import ModuleIndex

PAGE_OBJECT_PACKAGES = frozenset({"scrapy_poet", "web_poet", "zyte_common_items"})
FOLLOW_FUNCTIONS = frozenset({"follow", "follow_all"})


def is_request_construction(node: Call) -> bool:
    fn_name = get_func_name(node.func)
    return bool(
        fn_name
        and (
            fn_name.endswith("Request")
            or fn_name in {"follow", "follow_all", "replace"}
        ),
    )


def has_default_callback(node: Call) -> bool:
    """Tell whether *node* builds a request from scratch, and hence one that
    falls back to the ``parse`` callback."""
    fn_name = get_func_name(node.func)
    assert fn_name is not None
    return fn_name.endswith("Request") or fn_name in FOLLOW_FUNCTIONS


def is_response_meta(value: expr) -> bool:
    return (
        isinstance(value, Attribute)
        and value.attr == "meta"
        and isinstance(value.value, Name)
        and value.value.id == "response"
    )


def unwrap_annotation(annotation: expr) -> expr:
    """Return *annotation* without its surrounding :data:`typing.Annotated`."""
    if (
        isinstance(annotation, Subscript)
        and get_func_name(annotation.value) == "Annotated"
    ):
        index = annotation.slice
        if isinstance(index, Tuple) and index.elts:
            return index.elts[0]
    return annotation


def get_params(function: FunctionDef | AsyncFunctionDef) -> list[arg]:
    """Return the parameters of *function* without the instance one, so that
    the first one is the response parameter."""
    params = [*function.args.posonlyargs, *function.args.args]
    if params and params[0].arg in {"cls", "self"}:
        del params[0]
    return params + function.args.kwonlyargs


def is_dummy_response(function: FunctionDef | AsyncFunctionDef) -> bool:
    return any(
        param.annotation is not None
        and get_func_name(unwrap_annotation(param.annotation)) == "DummyResponse"
        for param in get_params(function)
    )


class RequestIssueFinder:
    def __init__(self, index: ModuleIndex) -> None:
        self.index = index

    def __call__(self, node: AST) -> Generator[Issue]:
        assert isinstance(node, Call)
        if not is_request_construction(node):
            return
        for arg_ in node.args:
            if is_response_meta(arg_):
                yield Issue(UNSAFE_META_COPY, Pos.from_node(arg_))
                break
        for kw in node.keywords:
            if is_response_meta(kw.value):
                yield Issue(UNSAFE_META_COPY, Pos.from_node(kw.value))
            elif kw.arg == "meta":
                yield from self.check_meta(kw.value, node)

    def check_meta(self, meta: expr, node: Call) -> Generator[Issue]:
        if not is_dict(meta):
            return
        assert isinstance(meta, (Call, Dict))
        automap: expr | None = None
        provider = False
        for key, value in iter_dict(meta):
            if not isinstance(key, Constant):
                continue
            if key.value == "zyte_api":
                yield Issue(ZYTE_RAW_PARAMS, Pos.from_node(key))
            elif key.value == "zyte_api_automap" and is_dict(value):
                automap = key
            elif key.value == "zyte_api_provider":
                provider = True
        if automap is not None:
            yield from self.check_automap(automap, node, provider=provider)

    def check_automap(
        self,
        key: expr,
        node: Call,
        *,
        provider: bool,
    ) -> Generator[Issue]:
        callback = self.get_callback(node)
        if callback is None:
            return
        if is_dummy_response(callback):
            yield Issue(UNUSED_AUTOMAP_PARAMS, Pos.from_node(key))
        elif not provider and self.has_page_object_params(callback):
            yield Issue(MISSING_PROVIDER_PARAMS, Pos.from_node(key))

    def get_callback(self, node: Call) -> FunctionDef | AsyncFunctionDef | None:
        """Return the definition of the callback of the *node* request, as long
        as it is defined in the same module."""
        name = None
        for kw in node.keywords:
            if kw.arg == "callback":
                name = get_func_name(kw.value)
                break
        else:
            if len(node.args) > 1:
                name = get_func_name(node.args[1])
            elif has_default_callback(node):
                name = "parse"
        return self.index.functions.get(name) if name else None

    def has_page_object_params(
        self,
        function: FunctionDef | AsyncFunctionDef,
    ) -> bool:
        return any(
            param.annotation is not None
            and self.index.package(unwrap_annotation(param.annotation))
            in PAGE_OBJECT_PACKAGES
            for param in get_params(function)[1:]
        )
