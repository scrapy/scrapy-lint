from __future__ import annotations

from packaging.utils import canonicalize_name
from packaging.version import Version

from scrapy_lint.data.apis import API_METHODS, API_PARAMETERS
from scrapy_lint.data.imports import IMPORTS
from scrapy_lint.data.packages import PACKAGES, VERSION_CONFLICTS
from scrapy_lint.data.settings import SETTINGS
from scrapy_lint.finders.settings.types import PATH_SUPPORT_VERSIONS
from scrapy_lint.settings import (
    MAX_DEFAULT_VALUE_HISTORY,
    SettingType,
    UnknownSettingValue,
)
from scrapy_lint.versions import UNKNOWN_UNSUPPORTED_VERSION, UnknownUnsupportedVersion

ALL_APIS = API_PARAMETERS + API_METHODS


def test_canonical_package_names():
    for name, data in SETTINGS.items():
        actual = data.package
        expected = canonicalize_name(actual)
        assert actual == expected, (
            f"Setting {name} uses non-canonical package name '{actual}', should be '{expected}'"
        )
    names = set(PACKAGES)
    names.update(api.package for api in ALL_APIS)
    for conflict in VERSION_CONFLICTS:
        names.update({conflict.package, conflict.dependency})
    for actual in names:
        expected = canonicalize_name(actual)
        assert actual == expected, (
            f"Package name {actual} is not canonical, should be '{expected}'"
        )


def test_api_versions():
    for api in ALL_APIS:
        deprecated_in = api.versioning.deprecated_in
        # Unlike settings, APIs are only checked from a known deprecation
        # version on.
        assert isinstance(deprecated_in, Version)
        removed_in = api.versioning.removed_in
        if removed_in:
            assert deprecated_in < removed_in
        if isinstance(api.discouraged_in, Version):
            assert api.discouraged_in < deprecated_in


def test_default_value_history():
    for data in SETTINGS.values():
        assert isinstance(data.name, str)
        default_value = data.default_value
        if isinstance(default_value, UnknownSettingValue):
            continue
        history = default_value.history
        if not history:
            continue
        assert UNKNOWN_UNSUPPORTED_VERSION in history
        assert len(history) == MAX_DEFAULT_VALUE_HISTORY or data.name.endswith("_BASE")


def test_enum_setting_values():
    for name, data in SETTINGS.items():
        if data.type != SettingType.ENUM_STR:
            continue
        assert data.values, f"Enum setting {name} has no values"


def test_path_support():
    for name, data in SETTINGS.items():
        if data.type is not SettingType.OPT_PATH:
            assert name not in PATH_SUPPORT_VERSIONS
        else:
            assert name in PATH_SUPPORT_VERSIONS


def test_import_replacements():
    for imported_object in IMPORTS.values():
        if imported_object.replacement:
            # The replacement is the guidance, so a second one would repeat it.
            assert not imported_object.versioning.sunset_guidance


def test_sunset_guidance():
    for data in SETTINGS.values():
        if not data.versioning.deprecated_in:
            assert not data.versioning.sunset_guidance
            assert not data.replacement


def test_replacement():
    for name, data in SETTINGS.items():
        if not data.replacement:
            continue
        assert data.replacement in SETTINGS, (
            f"Setting {name} is replaced by unknown setting {data.replacement}"
        )
        # The replacement is the sunset guidance, so having both would mean
        # reporting the same thing twice.
        assert not data.versioning.sunset_guidance
        assert data.value_replacements is None


def test_value_replacements():
    for name, data in SETTINGS.items():
        if data.value_replacements is None:
            continue
        assert data.versioning.deprecated_in
        for replacements in data.value_replacements.values():
            for replacement in replacements:
                assert replacement in SETTINGS, (
                    f"Setting {name} is replaced by unknown setting {replacement}"
                )


def test_versions():
    for data in SETTINGS.values():
        if data.versioning.removed_in:
            # A deprecated_in version is optional, for settings removed
            # without a prior deprecation, but it must be lower.
            if not data.versioning.deprecated_in:
                continue
            if isinstance(data.versioning.deprecated_in, UnknownUnsupportedVersion):
                assert data.versioning.deprecated_in is UNKNOWN_UNSUPPORTED_VERSION
                assert PACKAGES[data.package].lowest_supported_version
                assert (
                    PACKAGES[data.package].lowest_supported_version  # type: ignore[operator]
                    < data.versioning.removed_in
                )
            else:
                assert isinstance(data.versioning.deprecated_in, Version)
                assert data.versioning.deprecated_in < data.versioning.removed_in
