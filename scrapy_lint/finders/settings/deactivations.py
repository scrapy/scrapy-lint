from __future__ import annotations

from ast import Attribute, Call, Constant, Dict, Name, expr
from typing import TYPE_CHECKING, Any

from scrapy_lint.ast import is_dict, iter_dict
from scrapy_lint.data.settings import SETTINGS
from scrapy_lint.issues import (
    INVALID_COMPONENT_DEACTIVATION,
    REDUNDANT_SETTING_VALUE,
    Issue,
    Pos,
)
from scrapy_lint.settings import (
    UNKNOWN_SETTING_VALUE,
    Setting,
    SettingType,
    VersionedValue,
)

from .types import OBJECT_KEY_MATCHING_VERSION

if TYPE_CHECKING:
    from collections.abc import Callable, Generator

    from scrapy_lint.context import Project


class DeactivationChecker:
    """Check the keys of based dict settings that are set to None, across a
    settings module.

    Import paths are resolved with *resolve_import_path*.
    """

    def __init__(
        self,
        project: Project,
        resolve_import_path: Callable[[expr], str],
    ) -> None:
        self.project = project
        self.resolve_import_path = resolve_import_path
        self.unknown_addons = False
        self.noop_deactivations: list[tuple[str, str, Pos]] = []

    def note_unknown_addon(self) -> None:
        """Record that an add-on that scrapy-lint knows nothing about is
        enabled, and hence could be enabling any component."""
        self.unknown_addons = True

    def check(self, name: str, node: expr) -> Generator[Issue]:
        """Check the keys of *node*, the value of based setting *name*.

        Before Scrapy 2.15.0, a key disables a component of the base setting
        only if it is the same string the base setting uses, so an object key
        is reported for projects frozen to such a version. A key the base
        setting lacks is recorded, to be reported as redundant once the whole
        module is read and add-ons are known not to enable it either.
        """
        setting = SETTINGS.get(name)
        if (
            setting is None
            or setting.type
            not in {SettingType.BASED_COMP_PRIO_DICT, SettingType.BASED_OBJ_DICT}
            or not is_dict(node)
        ):
            return
        assert isinstance(node, (Call, Dict))
        base_keys = self.get_base_keys(setting)
        version = self.project.frozen_requirements.get("scrapy")
        object_keys_fail = version is not None and version < OBJECT_KEY_MATCHING_VERSION
        for key, value in iter_dict(node):
            if not isinstance(value, Constant) or value.value is not None:
                continue
            if isinstance(key, Constant) and isinstance(key.value, str):
                if key.value not in base_keys:
                    self.noop_deactivations.append(
                        (name, key.value, Pos.from_node(key)),
                    )
                continue
            if not isinstance(key, (Name, Attribute)):
                continue
            path = self.resolve_import_path(key)
            if path not in base_keys:
                self.noop_deactivations.append((name, path, Pos.from_node(key)))
            elif object_keys_fail:
                detail = (
                    f"before Scrapy {OBJECT_KEY_MATCHING_VERSION}, only {path!r} "
                    f"disables the base setting entry"
                )
                yield Issue(INVALID_COMPONENT_DEACTIVATION, Pos.from_node(key), detail)

    def get_base_keys(self, setting: Setting) -> set[str]:
        """Return the keys of the base setting of *setting* for the project
        Scrapy version, or for every known version when it is not frozen."""
        base = setting.base
        default = base.get_default_value(self.project)
        if default is not UNKNOWN_SETTING_VALUE:
            return set(default)
        assert isinstance(base.default_value, VersionedValue)
        return set().union(*base.default_value.history.values())

    def iter_issues(
        self, addon_settings: dict[str, tuple[Any, str]]
    ) -> Generator[Issue]:
        """Report keys set to None that neither the base setting nor a known
        add-on enables, unless an add-on scrapy-lint knows nothing about, or a
        known one that changes the setting, could be the one enabling them."""
        if self.unknown_addons:
            return
        for name, path, pos in self.noop_deactivations:
            if name in addon_settings:
                continue
            detail = f"{path!r} is not in {name}_BASE, so there is nothing to disable"
            yield Issue(REDUNDANT_SETTING_VALUE, pos, detail)
