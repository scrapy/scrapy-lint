from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from packaging.version import Version


@dataclass
class Package:
    highest_known_version: Version | None = None
    lowest_safe_version: Version | None = None
    lowest_supported_version: Version | None = None
    replacements: Sequence[str] | None = None


@dataclass
class VersionConflict:
    """A minimum version that *package* imposes on *dependency*.

    From *since* on, *package* requires *dependency* to be at least
    *lowest_compatible*.
    """

    package: str
    since: Version
    dependency: str
    lowest_compatible: Version
