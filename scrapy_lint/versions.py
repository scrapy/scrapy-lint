from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from scrapy_lint.data.packages import PACKAGES
from scrapy_lint.issues import DISCOURAGED_API, Issue

if TYPE_CHECKING:
    from packaging.version import Version

    from scrapy_lint.fixes import Fix
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
    # Guidance for uses that the removal broke, where migrating away from the
    # deprecation is no longer what they need, e.g. because the value that
    # sunset_guidance recommends is the only one left.
    removal_guidance: str | None = None
    # Version from which None became a valid value for a setting whose type
    # does not allow None otherwise.
    nullable_since: Version | None = None


@dataclass
class Sunset:
    """How to report an entry that its package deprecates or removes."""

    id_: tuple[int, str]
    detail: str
    removed: bool = False

    def issue(self, pos: Pos, *, subject: str = "", fix: Fix | None = None) -> Issue:
        """Build the issue to report at *pos*, naming *subject* for rules that
        report more than one kind of subject."""
        detail = f"{subject}, {self.detail}" if subject else self.detail
        return Issue(self.id_, pos, detail, fix=fix)


def check_sunset(
    entry,
    version: Version,
    deprecated_id: tuple[int, str],
    removed_id: tuple[int, str],
) -> Sunset | None:
    """Return how to report *entry*, whose package is frozen at *version*, as
    deprecated or removed, using *deprecated_id* or *removed_id* respectively,
    or as a discouraged API while it is worth avoiding but not deprecated yet,
    or ``None`` when there is nothing to report."""
    versioning = entry.versioning
    package = entry.package
    deprecated_in = versioning.deprecated_in
    if not deprecated_in:
        return None
    suffix = ""
    if isinstance(deprecated_in, UnknownUnsupportedVersion):
        deprecated_in = PACKAGES[package].lowest_supported_version
        assert deprecated_in
        suffix = " or lower"
    removed_in = versioning.removed_in
    removed = False
    if version < deprecated_in:
        if not is_discouraged(entry, version):
            return None
        id_ = DISCOURAGED_API
        detail = f"to be deprecated in {package} {deprecated_in}{suffix}"
    else:
        removed = removed_in is not None and version >= removed_in
        id_ = removed_id if removed else deprecated_id
        detail = f"deprecated in {package} {deprecated_in}{suffix}"
        if removed:
            detail += f", removed in {removed_in}"
    guidance = versioning.sunset_guidance
    if removed and versioning.removal_guidance:
        guidance = versioning.removal_guidance
    if guidance:
        detail += f"; {guidance}"
    return Sunset(id_, detail, removed=removed)


def is_discouraged(entry, version: Version) -> bool:
    """Return whether *entry* should be avoided already at *version*."""
    discouraged_in = getattr(entry, "discouraged_in", None)
    return discouraged_in is not None and (
        isinstance(discouraged_in, UnknownUnsupportedVersion)
        or version >= discouraged_in
    )
