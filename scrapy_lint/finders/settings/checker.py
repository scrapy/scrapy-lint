from __future__ import annotations

import ast
from ast import (
    Attribute,
    Call,
    ClassDef,
    Constant,
    Del,
    Dict,
    FunctionDef,
    GeneratorExp,
    Import,
    ImportFrom,
    Lambda,
    Load,
    Name,
    Store,
    Subscript,
    alias,
    expr,
    keyword,
)
from difflib import SequenceMatcher
from typing import TYPE_CHECKING, Any

from scrapy_lint.ast import definition_column, import_column, is_dict, iter_dict
from scrapy_lint.data.packages import PACKAGES
from scrapy_lint.data.settings import (
    MAX_AUTOMATIC_SUGGESTIONS,
    MIN_AUTOMATIC_SUGGESTION_SCORE,
    PREDEFINED_SUGGESTIONS,
    SETTINGS,
)
from scrapy_lint.fixes import Edit, Fix
from scrapy_lint.issues import (
    BASE_SETTING_USE,
    DEPRECATED_SETTING,
    INVALID_SETTING_VALUE,
    LOWERCASE_SETTING,
    MISSING_SETTING_REQUIREMENT,
    NO_OP_SETTING_UPDATE,
    NON_PICKLABLE_SETTING,
    REMOVED_SETTING,
    SETTING_NEEDS_UPGRADE,
    UNKNOWN_SETTING,
    WRONG_SETTING_METHOD,
    ZYTE_RAW_PARAMS,
    Issue,
    Pos,
)
from scrapy_lint.settings import (
    SETTING_GETTERS,
    SETTING_TYPE_GETTERS,
    SETTING_UPDATER_TYPES,
    SETTING_UPDATERS,
    Setting,
)
from scrapy_lint.versions import UnknownUnsupportedVersion, check_sunset

from .types import TYPE_CHECKERS, is_allowed_none
from .values import VALUE_CHECKERS, check_secret

if TYPE_CHECKING:
    from collections.abc import Generator

    from scrapy_lint.addons import Addon
    from scrapy_lint.context import Context

    AddonEntry = tuple[Addon, str, float, expr]

LineNumber = int
SESSION_SETTINGS = frozenset(
    {
        "ZYTE_API_SESSION_ENABLED",
        "ZYTE_API_SESSION_POOL_SIZE",
        "ZYTE_API_SESSION_POOLS",
    },
)
IssueNode = Constant | Name | keyword | ClassDef | FunctionDef | Import | ImportFrom


def build_rename_fix(setting: Setting, node: IssueNode | None) -> Fix | None:
    """Build a fix that renames *node*, which spells the name of *setting*, as
    the setting that replaces it.

    Returns ``None`` (report only, no fix) when the setting has no replacement,
    or when *node* is not a plain name or single-quoted string literal, e.g. a
    class definition or an import.
    """
    if not setting.replacement:
        return None
    assert isinstance(setting.name, str)
    length = len(setting.name)
    if isinstance(node, Name):
        start = Pos.from_node(node)
        end = Pos(start.line, start.column + length)
    elif (
        isinstance(node, Constant)
        and node.lineno == node.end_lineno
        and node.end_col_offset == node.col_offset + length + 2
    ):
        start = Pos(node.lineno, node.col_offset + 1)
        end = Pos(node.lineno, node.end_col_offset - 1)
    else:
        return None
    return Fix(
        [Edit(start, end, setting.replacement)],
        message=f"rename {setting.name} to {setting.replacement}",
    )


class SettingChecker:
    def __init__(self, context: Context) -> None:
        self.context = context
        self.project = context.project
        self.additional_known_settings = set(context.options.get("known-settings", []))
        self.in_update_pre_crawler_settings = False
        self.in_update_settings = False
        self.source: str | None = None

    def is_known_setting(self, name: str) -> bool:
        return name in SETTINGS or name in self.additional_known_settings

    def check_lowercase_name(self, name: str, pos: Pos) -> Generator[Issue]:
        upper = name.upper()
        if upper != name and self.is_known_setting(upper):
            yield Issue(LOWERCASE_SETTING, pos, f"did you mean: {upper}?")

    def is_supported_setting(self, name: str) -> bool:
        if not self.project.packages or name not in SETTINGS:
            return True
        setting = SETTINGS[name]
        if setting.package not in self.project.frozen_requirements or (
            not setting.versioning.added_in and not setting.versioning.deprecated_in
        ):
            return setting.package in self.project.packages
        deprecated_in = setting.versioning.deprecated_in
        if isinstance(deprecated_in, UnknownUnsupportedVersion):
            deprecated_in = PACKAGES[setting.package].lowest_supported_version
            assert deprecated_in
        package_version = self.project.frozen_requirements[setting.package]
        return (
            not setting.versioning.added_in
            or package_version >= setting.versioning.added_in
        ) and (not deprecated_in or package_version < deprecated_in)

    def suggest_names(self, unknown_name: str) -> list[str]:
        if unknown_name in PREDEFINED_SUGGESTIONS:
            return [
                setting
                for setting in PREDEFINED_SUGGESTIONS[unknown_name]
                if self.is_supported_setting(setting)
            ]
        matches = []
        for candidate in self.additional_known_settings | set(SETTINGS):
            if (
                candidate.endswith("_BASE") and not unknown_name.endswith("_BASE")
            ) or not self.is_supported_setting(candidate):
                continue
            ratio = SequenceMatcher(None, unknown_name, candidate).ratio()
            if ratio >= MIN_AUTOMATIC_SUGGESTION_SCORE:
                matches.append((candidate, ratio))
        matches.sort(key=lambda x: (-x[1], x[0]))
        return [m[0] for m in matches[:MAX_AUTOMATIC_SUGGESTIONS]]

    def check_known_name(
        self,
        name: str,
        pos: Pos,
        node: IssueNode | None = None,
    ) -> Generator[Issue]:
        yield from self.check_special_names(name, pos)
        if name not in SETTINGS:
            return
        setting = SETTINGS[name]
        package = setting.package
        yield from self.check_setting_requirement(setting, pos)
        if package not in self.project.frozen_requirements:
            return
        yield from self.check_setting_versioning(setting, pos, node)

    def check_special_names(self, name: str, pos: Pos) -> Generator[Issue]:
        if name.endswith("_BASE"):
            yield Issue(BASE_SETTING_USE, pos)
        elif name == "ZYTE_API_DEFAULT_PARAMS":
            yield Issue(ZYTE_RAW_PARAMS, pos)

    def check_setting_requirement(self, setting, pos: Pos) -> Generator[Issue]:
        package = setting.package
        if (
            package not in self.project.frozen_requirements
            and self.project.packages
            and package not in self.project.packages
        ):
            yield Issue(MISSING_SETTING_REQUIREMENT, pos, package)

    def check_setting_versioning(
        self,
        setting,
        pos: Pos,
        node: IssueNode | None = None,
    ) -> Generator[Issue]:
        package = setting.package
        added_in = setting.versioning.added_in
        version = self.project.frozen_requirements[package]
        if added_in and version < added_in:
            yield Issue(SETTING_NEEDS_UPGRADE, pos, f"added in {package} {added_in}")
            return
        sunset = check_sunset(setting, version, DEPRECATED_SETTING, REMOVED_SETTING)
        if sunset is not None:
            yield sunset.issue(pos, fix=build_rename_fix(setting, node))

    def check_dict(self, node: expr) -> Generator[Issue]:
        if not is_dict(node):
            return
        assert isinstance(node, (Call, Dict))
        for key, value in iter_dict(node):
            if not isinstance(key, Constant):
                continue
            yield from self.check_name(key)
            yield from self.check_update(key)
            if isinstance(key.value, str):
                yield from self.check_value(key.value, value)

    def check_name(
        self,
        node: Constant
        | Name
        | keyword
        | ClassDef
        | FunctionDef
        | tuple[Import | ImportFrom, alias],
    ) -> Generator[Issue]:
        resolved_node: IssueNode
        name: Any
        if isinstance(node, tuple):
            resolved_node, import_alias = node
            name = import_alias.asname or import_alias.name
        else:
            resolved_node = node
            import_alias = None
            name = (
                resolved_node.value
                if isinstance(resolved_node, Constant)
                else resolved_node.id
                if isinstance(resolved_node, Name)
                else resolved_node.arg
                if isinstance(resolved_node, keyword)
                else resolved_node.name
            )
        if not isinstance(name, str):
            return  # Not a string, so not a setting name
        if isinstance(resolved_node, (Import, ImportFrom)):
            assert import_alias
            column = import_column(import_alias)
        elif isinstance(resolved_node, (ClassDef, FunctionDef)):
            column = definition_column(resolved_node)
        else:
            column = resolved_node.col_offset
        pos = Pos.from_node(resolved_node, column)
        yield from self.check_name_str(name, pos, resolved_node)

    def check_name_str(
        self,
        name: str,
        pos: Pos,
        node: IssueNode | None = None,
    ) -> Generator[Issue]:
        if not self.is_known_setting(name):
            detail = None
            if suggestions := self.suggest_names(name):
                detail = f"did you mean: {', '.join(suggestions)}?"
            yield Issue(UNKNOWN_SETTING, pos, detail)
            return
        yield from self.check_known_name(name, pos, node)

    def check_update(self, node: keyword | Constant) -> Generator[Issue]:
        name = node.value if isinstance(node, Constant) else node.arg
        if not isinstance(name, str) or name not in SETTINGS:
            return
        setting = SETTINGS[name]
        if setting.is_pre_crawler and not self.in_update_pre_crawler_settings:
            yield Issue(NO_OP_SETTING_UPDATE, Pos.from_node(node))

    def check_method(self, name_node: Constant, call: Call) -> Generator[Issue]:
        func = call.func
        assert isinstance(func, Attribute)
        name = name_node.value
        assert isinstance(name, str)
        if name not in SETTINGS:
            return
        setting = SETTINGS[name]
        name_pos = Pos.from_node(name_node)
        if (
            func.attr in SETTING_UPDATERS
            and setting.is_pre_crawler
            and not self.in_update_pre_crawler_settings
        ):
            yield Issue(NO_OP_SETTING_UPDATE, name_pos)
        yield from self.check_wrong_setting_method(setting, call, name_pos)

    def check_wrong_setting_method(
        self,
        setting: Setting,
        call: Call,
        name_pos: Pos,
    ) -> Generator[Issue]:
        func = call.func
        assert isinstance(func, Attribute)
        if (
            setting.type is not None
            and func.attr in SETTING_UPDATER_TYPES
            and setting.type not in SETTING_UPDATER_TYPES[func.attr]
        ):
            yield Issue(WRONG_SETTING_METHOD, name_pos)
        if func.attr not in SETTING_GETTERS or setting.type is None:
            return
        assert func.end_col_offset is not None
        column = func.end_col_offset - len(func.attr)
        pos = Pos.from_node(func, column)
        if setting.type in SETTING_TYPE_GETTERS:
            expected = SETTING_TYPE_GETTERS[setting.type]
            if func.attr != expected and (
                expected != "getwithbase" or not self.in_update_settings
            ):
                yield Issue(WRONG_SETTING_METHOD, pos, f"use {expected}()")
        elif func.attr not in {"get", "__getitem__"}:
            has_default = False
            if len(call.args) > 1:
                has_default = True
            else:
                for kw in call.keywords:
                    if kw.arg == "default":
                        has_default = True
                        break
            if has_default:
                yield Issue(WRONG_SETTING_METHOD, pos, "use get()")
            else:
                yield Issue(WRONG_SETTING_METHOD, pos, "use []")

    def check_subscript(self, name: str, node: Subscript) -> Generator[Issue]:
        if name not in SETTINGS:
            return
        setting = SETTINGS[name]
        if isinstance(node.ctx, Load):
            yield from self.check_subscript_read(setting, node)
        if (
            isinstance(node.ctx, (Store, Del))
            and setting.is_pre_crawler
            and not self.in_update_pre_crawler_settings
        ):
            column = getattr(node.slice, "col_offset", node.col_offset + 1)
            yield Issue(NO_OP_SETTING_UPDATE, Pos.from_node(node, column))

    def check_subscript_read(
        self, setting: Setting, node: Subscript
    ) -> Generator[Issue]:
        if (
            setting.type is not None
            and setting.type in SETTING_TYPE_GETTERS
            and (
                SETTING_TYPE_GETTERS[setting.type] != "getwithbase"
                or not self.in_update_settings
            )
        ):
            if isinstance(node.value, Name):
                column = node.value.col_offset + len(node.value.id)
            else:
                assert isinstance(node.value, Attribute)
                assert node.value.end_col_offset is not None
                column = node.value.end_col_offset - len(node.value.attr)
            expected = SETTING_TYPE_GETTERS[setting.type]
            pos = Pos.from_node(node, column)
            yield Issue(WRONG_SETTING_METHOD, pos, f"use {expected}()")

    def is_materializer_call(self, parent):
        if not isinstance(parent, Call):
            return False
        func = parent.func
        return isinstance(func, Name) and func.id in {"list", "tuple", "set"}

    def check_non_picklable(self, node, parent=None):
        if isinstance(node, Lambda) or (
            isinstance(node, GeneratorExp) and not self.is_materializer_call(parent)
        ):
            yield Issue(NON_PICKLABLE_SETTING, Pos.from_node(node))
        for child in ast.iter_child_nodes(node):
            yield from self.check_non_picklable(child, node)

    def check_value(self, name: str, node: expr) -> Generator[Issue]:
        invalid = False
        if name in VALUE_CHECKERS:
            for issue in VALUE_CHECKERS[name](node, context=self.context):
                invalid |= issue.code == INVALID_SETTING_VALUE[0]
                yield issue

        yield from self.check_non_picklable(node)

        if name not in SETTINGS:
            return
        setting = SETTINGS[name]
        # A value that is not even a valid credential is not a leaked one.
        if setting.is_secret and not invalid:
            yield from check_secret(node, setting=setting, project=self.project)
        if (
            not invalid
            and setting.type is not None
            and not is_allowed_none(node, setting, self.project)
        ):
            yield from TYPE_CHECKERS[setting.type](
                node,
                setting=setting,
                project=self.project,
                source=self.source,
            )
