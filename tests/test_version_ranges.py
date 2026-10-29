from __future__ import annotations

import pytest
from packaging.requirements import Requirement
from packaging.version import Version

from scrapy_lint.requirements import version_range
from scrapy_lint.versions import VersionRange


def parse(*lines: str) -> VersionRange:
    return version_range([Requirement(line) for line in lines])


@pytest.mark.parametrize(
    ("lines", "expected"),
    [
        (("scrapy",), VersionRange()),
        (("scrapy==2.11.2",), VersionRange(Version("2.11.2"), Version("2.11.2"))),
        (("scrapy===2.11.2",), VersionRange(Version("2.11.2"), Version("2.11.2"))),
        (("scrapy===2.11.2.custom",), VersionRange()),
        (("scrapy==2.11.*",), VersionRange(Version("2.11"), Version("2.12"), False)),
        (("scrapy>=2.11",), VersionRange(Version("2.11"))),
        (("scrapy>2.11",), VersionRange(Version("2.11"))),
        (("scrapy<=2.13",), VersionRange(None, Version("2.13"))),
        (("scrapy<2.13",), VersionRange(None, Version("2.13"), False)),
        (("scrapy!=2.12",), VersionRange()),
        (("scrapy~=2.11",), VersionRange(Version("2.11"), Version("3"), False)),
        (("scrapy~=2.11.0",), VersionRange(Version("2.11.0"), Version("2.12"), False)),
        (
            ("scrapy>=2.11,<2.13",),
            VersionRange(Version("2.11"), Version("2.13"), False),
        ),
        # Bounds from several lines narrow each other down.
        (
            ("scrapy>=2.11", "scrapy>=2.12", "scrapy<=2.14", "scrapy<=2.13"),
            VersionRange(Version("2.12"), Version("2.13")),
        ),
        # An exclusive bound wins over an inclusive one for the same version.
        (
            ("scrapy<=2.13", "scrapy<2.13"),
            VersionRange(None, Version("2.13"), False),
        ),
        # Requirements that only apply under a marker do not constrain the
        # range.
        (("scrapy<2.13; python_version < '3.11'",), VersionRange()),
    ],
)
def test_version_range(lines, expected):
    assert parse(*lines) == expected


@pytest.mark.parametrize(
    ("range_", "version", "allows_below", "allows_at_least", "requires_upgrade"),
    [
        (VersionRange(), "2.12", True, True, False),
        (VersionRange(Version("2.12")), "2.12", False, True, False),
        (VersionRange(Version("2.11")), "2.12", True, True, True),
        (VersionRange(None, Version("2.12")), "2.12", True, True, False),
        (VersionRange(None, Version("2.12"), False), "2.12", True, False, False),
        (VersionRange(None, Version("2.11")), "2.12", True, False, False),
        (
            VersionRange(Version("2.12"), Version("2.12")),
            "2.12",
            False,
            True,
            False,
        ),
    ],
)
def test_predicates(range_, version, allows_below, allows_at_least, requires_upgrade):
    version = Version(version)
    assert range_.allows_below(version) is allows_below
    assert range_.allows_at_least(version) is allows_at_least
    assert range_.requires_upgrade(version) is requires_upgrade


@pytest.mark.parametrize(
    ("range_", "expected"),
    [
        (VersionRange(), "any scrapy version"),
        (VersionRange(Version("2.11"), Version("2.11")), "scrapy 2.11"),
        (VersionRange(Version("2.11")), "scrapy >=2.11"),
        (VersionRange(None, Version("2.13")), "scrapy <=2.13"),
        (VersionRange(None, Version("2.13"), False), "scrapy <2.13"),
        (
            VersionRange(Version("2.11"), Version("2.13"), False),
            "scrapy >=2.11,<2.13",
        ),
    ],
)
def test_describe(range_, expected):
    assert range_.describe("scrapy") == expected
