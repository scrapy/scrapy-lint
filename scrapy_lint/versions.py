from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from scrapy_lint.data.packages import PACKAGES
from scrapy_lint.issues import Issue

if TYPE_CHECKING:
    from collections.abc import Generator

    from packaging.version import Version

    from scrapy_lint.issues import Pos


class UnknownUnsupportedVersion:  # pylint: disable=too-few-public-methods
    pass


class UnknownFutureVersion:  # pylint: disable=too-few-public-methods
    pass


UNKNOWN_UNSUPPORTED_VERSION = UnknownUnsupportedVersion()
UNKNOWN_FUTURE_VERSION = UnknownFutureVersion()


@dataclass
class Versioning:
    added_in: Version | None = None
    deprecated_in: Version | UnknownUnsupportedVersion | None = None
    removed_in: Version | None = None
    sunset_guidance: str | None = None


def check_sunset(
    entry,
    version: Version,
    pos: Pos,
    deprecated_id: tuple[int, str],
    removed_id: tuple[int, str],
) -> Generator[Issue]:
    """Report *entry*, whose package is frozen at *version*, as deprecated or
    removed, using *deprecated_id* or *removed_id* respectively."""
    versioning = entry.versioning
    package = entry.package
    deprecated_in = versioning.deprecated_in
    if not deprecated_in:
        return
    suffix = ""
    if isinstance(deprecated_in, UnknownUnsupportedVersion):
        deprecated_in = PACKAGES[package].lowest_supported_version
        assert deprecated_in
        suffix = " or lower"
    if version < deprecated_in:
        return
    detail = f"deprecated in {package} {deprecated_in}{suffix}"
    removed_in = versioning.removed_in
    if removed_in and version >= removed_in:
        detail += f", removed in {removed_in}"
        id_ = removed_id
    else:
        id_ = deprecated_id
    if versioning.sunset_guidance:
        detail += f"; {versioning.sunset_guidance}"
    yield Issue(id_, pos, detail)
