from packaging.version import Version

from scrapy_lint.addons import Default, VersionedSettings
from scrapy_lint.data.addons import ADDONS
from scrapy_lint.settings import UNKNOWN_SETTING_VALUE
from scrapy_lint.versions import UNKNOWN_UNSUPPORTED_VERSION


def test_all_time_settings():
    settings = VersionedSettings(
        history={
            UNKNOWN_UNSUPPORTED_VERSION: {"AGREED": 1, "DISPUTED": 1, "DROPPED": 1},
            Version("2.0.0"): {"AGREED": 1, "DISPUTED": 2},
        },
    )
    assert settings.all_time_settings == {
        "AGREED": 1,
        "DISPUTED": UNKNOWN_SETTING_VALUE,
    }


def test_unsupported_version():
    settings = ADDONS["scrapy_zyte_api.Addon"].settings
    assert settings[Version("0.1.0")] is settings.history[UNKNOWN_UNSUPPORTED_VERSION]


def test_known_version():
    settings = ADDONS["scrapy_zyte_api.Addon"].settings
    assert settings[Version("0.36.0")]["ZYTE_API_TRANSPARENT_MODE"] is True


def test_after():
    packages = {addon.package for addon in ADDONS.values()}
    for addon in ADDONS.values():
        assert addon.after <= packages - {addon.package}


def test_default_equality():
    assert Default({"a": 1}) == Default({"a": 1})
    assert Default({"a": 1}) != Default({"a": 2})
    assert Default({"a": 1}) != {"a": 1}


def test_default_repr():
    assert repr(Default({"a": 1})) == "Default({'a': 1})"


def test_default_merge():
    settings = VersionedSettings(
        history={
            UNKNOWN_UNSUPPORTED_VERSION: {"MIDDLEWARES": Default({"a": 1})},
            Version("2.0.0"): {"MIDDLEWARES": Default({"a": 1})},
        },
    )
    assert settings.all_time_settings == {"MIDDLEWARES": Default({"a": 1})}


def test_known_version_default():
    settings = ADDONS["scrapy_zyte_api.Addon"].settings
    value = settings[Version("0.36.0")]["DOWNLOADER_MIDDLEWARES"]
    assert isinstance(value, Default)
    assert not isinstance(settings[Version("0.36.0")]["DOWNLOAD_HANDLERS"], Default)
