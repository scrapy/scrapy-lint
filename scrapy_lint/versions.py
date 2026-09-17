from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from scrapy_lint.data.packages import PACKAGES
from scrapy_lint.issues import DISCOURAGED_API, Issue

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
    # Version that reverted the deprecation.
    undeprecated_in: Version | None = None
    sunset_guidance: str | None = None
    # Version from which None became a valid value for a setting whose type
    # does not allow None otherwise.
    nullable_since: Version | None = None


def check_sunset(
    entry,
    version: Version,
    pos: Pos,
    deprecated_id: tuple[int, str],
    removed_id: tuple[int, str],
) -> Generator[Issue]:
    """Report *entry*, whose package is frozen at *version*, as deprecated or
    removed, using *deprecated_id* or *removed_id* respectively, or as a
    discouraged API while it is worth avoiding but not deprecated yet."""
    versioning = entry.versioning
    package = entry.package
    deprecated_in = versioning.deprecated_in
    if not deprecated_in:
        return
    undeprecated_in = versioning.undeprecated_in
    if undeprecated_in and version >= undeprecated_in:
        return
    suffix = ""
    if isinstance(deprecated_in, UnknownUnsupportedVersion):
        deprecated_in = PACKAGES[package].lowest_supported_version
        assert deprecated_in
        suffix = " or lower"
    if version < deprecated_in:
        if not is_discouraged(entry, version):
            return
        id_ = DISCOURAGED_API
        detail = f"to be deprecated in {package} {deprecated_in}{suffix}"
    else:
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


def is_discouraged(entry, version: Version) -> bool:
    """Return whether *entry* should be avoided already at *version*."""
    discouraged_in = getattr(entry, "discouraged_in", None)
    return discouraged_in is not None and (
        isinstance(discouraged_in, UnknownUnsupportedVersion)
        or version >= discouraged_in
    )
