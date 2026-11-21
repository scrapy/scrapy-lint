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
    # Version that reverted the deprecation.
    undeprecated_in: Version | None = None
    sunset_guidance: str | None = None
    # Guidance for uses that the removal broke, where migrating away from the
    # deprecation is no longer what they need, e.g. because the value that
    # sunset_guidance recommends is the only one left.
    removal_guidance: str | None = None
    # Version from which None became a valid value for a setting whose type
    # does not allow None otherwise.
    nullable_since: Version | None = None


@dataclass(frozen=True)
class VersionRange:
    """Versions of a package that a project may be installed with, as declared
    in its requirements.

    *lowest* and *highest* are ``None`` when the requirement declares no
    minimum or no maximum version, respectively, and *highest_inclusive* is
    ``False`` when the maximum version is itself excluded, as in ``<2.13``.
    """

    lowest: Version | None = None
    highest: Version | None = None
    highest_inclusive: bool = True

    @property
    def pinned(self) -> Version | None:
        """Single version this range is frozen to, if any."""
        if self.lowest is not None and self.lowest == self.highest:
            return self.lowest
        return None

    def allows_below(self, version: Version) -> bool:
        """Return whether some allowed version is lower than *version*.

        An undeclared minimum version counts as allowing any lower version.
        """
        return self.lowest is None or self.lowest < version

    def allows_at_least(self, version: Version) -> bool:
        """Return whether some allowed version is *version* or higher."""
        if self.highest is None:
            return True
        return self.highest > version or (
            self.highest_inclusive and self.highest == version
        )

    def requires_upgrade(self, version: Version) -> bool:
        """Return whether the declared minimum version is lower than
        *version*.

        Unlike :meth:`allows_below`, an undeclared minimum version is not a
        claim of support for lower versions, and hence not a reason to upgrade.
        """
        return self.lowest is not None and self.lowest < version

    def describe(self, package: str) -> str:
        """Return a description of this range as a requirement specifier, e.g.
        ``scrapy >=2.11,<2.13``."""
        if self.pinned:
            return f"{package} {self.pinned}"
        specifiers = []
        if self.lowest:
            specifiers.append(f">={self.lowest}")
        if self.highest:
            operator = "<=" if self.highest_inclusive else "<"
            specifiers.append(f"{operator}{self.highest}")
        if not specifiers:
            return f"any {package} version"
        return f"{package} {','.join(specifiers)}"

    def support_detail(self, package: str) -> str:
        """Return a detail suffix stating which versions the project supports,
        empty for a frozen version."""
        if self.pinned:
            return ""
        return f"; this project supports {self.describe(package)}"


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
    versions: VersionRange,
    deprecated_id: tuple[int, str],
    removed_id: tuple[int, str],
) -> Sunset | None:
    """Return how to report *entry*, whose package the project allows at
    *versions*, as deprecated or removed, using *deprecated_id* or
    *removed_id* respectively, or as a discouraged API while it is worth
    avoiding but not deprecated yet, or ``None`` when there is nothing to
    report."""
    versioning = entry.versioning
    package = entry.package
    deprecated_in = versioning.deprecated_in
    removed_in = versioning.removed_in
    removed = False
    if not deprecated_in:
        if not removed_in or not versions.allows_at_least(removed_in):
            return None
        removed = True
        id_ = removed_id
        detail = f"removed in {package} {removed_in}"
    else:
        undeprecated_in = versioning.undeprecated_in
        if undeprecated_in and not versions.allows_below(undeprecated_in):
            return None
        suffix = ""
        if isinstance(deprecated_in, UnknownUnsupportedVersion):
            deprecated_in = PACKAGES[package].lowest_supported_version
            assert deprecated_in
            suffix = " or lower"
        if not versions.allows_at_least(deprecated_in):
            if not is_discouraged(entry, versions):
                return None
            id_ = DISCOURAGED_API
            detail = f"to be deprecated in {package} {deprecated_in}{suffix}"
        else:
            removed = removed_in is not None and versions.allows_at_least(removed_in)
            id_ = removed_id if removed else deprecated_id
            detail = f"deprecated in {package} {deprecated_in}{suffix}"
            if removed:
                detail += f", removed in {removed_in}"
    detail += versions.support_detail(package)
    guidance = versioning.sunset_guidance
    if removed and versioning.removal_guidance:
        guidance = versioning.removal_guidance
    if not guidance and (replacement := getattr(entry, "replacement", None)):
        guidance = f"use {replacement} instead"
    if guidance:
        detail += f"; {guidance}"
    return Sunset(id_, detail, removed=removed)


def is_discouraged(entry, versions: VersionRange) -> bool:
    """Return whether *entry* should be avoided already at *versions*."""
    discouraged_in = getattr(entry, "discouraged_in", None)
    return discouraged_in is not None and (
        isinstance(discouraged_in, UnknownUnsupportedVersion)
        or versions.allows_at_least(discouraged_in)
    )
