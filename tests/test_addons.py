from packaging.version import Version

from scrapy_lint.addons import VersionedSettings
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
