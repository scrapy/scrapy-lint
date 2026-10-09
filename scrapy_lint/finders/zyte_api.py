from __future__ import annotations

from ast import Assign, Call, ClassDef, Constant, Dict, Name
from typing import TYPE_CHECKING, Any

from scrapy_lint.ast import extract_literal_value, is_dict, iter_dict
from scrapy_lint.issues import INCONSISTENT_ZYTE_API_PARAMS, Issue, Pos

if TYPE_CHECKING:
    from ast import AST, expr
    from collections.abc import Generator, Mapping

    from scrapy_lint.context import Context

AUTOMAP_PARAMS = "ZYTE_API_AUTOMAP_PARAMS"
PROVIDER_PARAMS = "ZYTE_API_PROVIDER_PARAMS"
PARAM_SETTINGS = (AUTOMAP_PARAMS, PROVIDER_PARAMS)

GLOBAL_PARAMS = ("geolocation", "ipType")
"""Zyte API params that are meant to apply to every request of a project."""

_UNKNOWN = object()

_Param = tuple[Pos, Any]


def _find_param(node: expr | None, param: str) -> _Param | None:
    """Return the position and value of *param* in the *node* mapping."""
    if node is None:
        return None
    assert isinstance(node, (Call, Dict))
    for key, value in iter_dict(node):
        if not isinstance(key, Constant) or key.value != param:
            continue
        literal, is_literal = extract_literal_value(value)
        return Pos.from_node(key), literal if is_literal else _UNKNOWN
    return None


def _report_pos(
    found: Mapping[str, _Param | None],
    local: Mapping[str, tuple[expr, Pos]],
) -> Pos:
    """Return where to report a mismatch of the *found* params.

    The setting that lacks the param comes first, since that is the one to
    edit, and it is reported at its own position rather than at the param.
    """
    name = next(
        name
        for name in sorted(PARAM_SETTINGS, key=lambda name: found[name] is not None)
        if name in local
    )
    param = found[name]
    return param[0] if param else local[name][1]


def find_param_issues(
    local: Mapping[str, tuple[expr, Pos]],
    inherited: Mapping[str, expr],
    *,
    provider: bool,
) -> Generator[Issue]:
    """Report global params that automap and provider requests do not share.

    *local* maps the param settings that the checked place defines to their
    value and the position to report them at, *inherited* maps setting names
    that the settings module defines to their value, and *provider* tells
    whether the project uses the scrapy-poet provider.
    """
    nodes = {
        name: local[name][0] if name in local else inherited.get(name)
        for name in PARAM_SETTINGS
    }
    if any(node is not None and not is_dict(node) for node in nodes.values()):
        # A value that is not a literal mapping could hold any param.
        return
    if nodes[PROVIDER_PARAMS] is None and not provider:
        return
    for param in GLOBAL_PARAMS:
        found = {name: _find_param(nodes[name], param) for name in PARAM_SETTINGS}
        automap, provider_param = found[AUTOMAP_PARAMS], found[PROVIDER_PARAMS]
        if automap is None and provider_param is None:
            continue
        if automap and provider_param:
            if _UNKNOWN in (automap[1], provider_param[1]):
                continue
            if automap[1] == provider_param[1]:
                continue
            detail = (
                f"{param} is {automap[1]!r} in {AUTOMAP_PARAMS} and "
                f"{provider_param[1]!r} in {PROVIDER_PARAMS}"
            )
        else:
            missing = PROVIDER_PARAMS if automap else AUTOMAP_PARAMS
            detail = f"{param} is missing from {missing}"
        yield Issue(INCONSISTENT_ZYTE_API_PARAMS, _report_pos(found, local), detail)


class ZyteAPIParamIssueFinder:  # pylint: disable=too-few-public-methods
    def __init__(self, context: Context) -> None:
        self.context = context

    def __call__(self, node: AST) -> Generator[Issue]:
        assert isinstance(node, ClassDef)
        for child in node.body:
            if not isinstance(child, Assign) or not any(
                isinstance(target, Name) and target.id == "custom_settings"
                for target in child.targets
            ):
                continue
            yield from self._check_custom_settings(child.value)

    def _check_custom_settings(self, node: expr) -> Generator[Issue]:
        if not is_dict(node):
            return
        assert isinstance(node, (Call, Dict))
        local = {}
        for key, value in iter_dict(node):
            if isinstance(key, Constant) and key.value in PARAM_SETTINGS:
                local[key.value] = (value, Pos.from_node(key))
        if not local:
            return
        project = self.context.project
        yield from find_param_issues(
            local,
            project.setting_module_values,
            provider=project.uses_scrapy_poet,
        )
