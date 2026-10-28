from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from scrapy_lint.settings import UNKNOWN_SETTING_VALUE
from scrapy_lint.versions import (
    UNKNOWN_UNSUPPORTED_VERSION,
    UnknownFutureVersion,
    UnknownUnsupportedVersion,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

    from packaging.version import Version

    from scrapy_lint.context import Project


class Default:  # pylint: disable=too-few-public-methods
    """Wraps the value of a dict-valued setting an add-on only fills entries
    of that are not already present, e.g. through ``BaseSettings.setdefault``
    or an equivalent per-entry check.

    Restating one of those entries can be a deliberate way to keep it stable
    across add-on upgrades, unlike restating an entry the add-on always
    overwrites.
    """

    __slots__ = ("value",)
    __hash__ = None  # type: ignore[assignment]

    def __init__(self, value: dict[Any, Any]):
        self.value = value

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Default) and self.value == other.value

    def __repr__(self) -> str:
        return f"Default({self.value!r})"


# The settings an add-on changes, mapped to the value it sets them to, or to
# UNKNOWN_SETTING_VALUE when that value cannot be relied on, e.g. because it
# depends on the value of other settings. A dict value wrapped in Default is
# only set when the setting does not already have that entry.
AddonSettings = dict[str, Any]


def _merge_settings(snapshots: Iterable[AddonSettings]) -> AddonSettings:
    """Return the settings that every snapshot in *snapshots* changes, mapped
    to the value they all set, or to UNKNOWN_SETTING_VALUE when they differ."""
    snapshots = list(snapshots)
    names = set.intersection(*(set(snapshot) for snapshot in snapshots))
    result = {}
    for name in names:
        values = [snapshot[name] for snapshot in snapshots]
        result[name] = (
            values[0]
            if all(value == values[0] for value in values[1:])
            else UNKNOWN_SETTING_VALUE
        )
    return result


class VersionedSettings:  # pylint: disable=too-few-public-methods
    def __init__(
        self,
        history: dict[
            Version | UnknownUnsupportedVersion | UnknownFutureVersion, AddonSettings
        ],
    ):
        self.history = history
        # What the add-on does in every version it is known for, for projects
        # that do not pin it to a single version.
        self.all_time_settings: AddonSettings = _merge_settings(history.values())

    def __getitem__(self, version: Version) -> AddonSettings:
        applicable_versions = [
            v
            for v in self.history
            if not isinstance(v, UnknownUnsupportedVersion)
            and not isinstance(v, UnknownFutureVersion)
            and v <= version
        ]
        if not applicable_versions:
            assert UNKNOWN_UNSUPPORTED_VERSION in self.history
            return self.history[UNKNOWN_UNSUPPORTED_VERSION]
        latest_applicable = max(applicable_versions)
        return self.history[latest_applicable]


@dataclass
class Addon:
    package: str
    settings: VersionedSettings
    after: frozenset[str] = frozenset()
    """Packages whose add-on must run before this one."""

    def get_settings(self, project: Project) -> AddonSettings:
        if self.package not in project.frozen_requirements:
            return self.settings.all_time_settings
        version = project.frozen_requirements[self.package]
        return self.settings[version]
