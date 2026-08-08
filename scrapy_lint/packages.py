from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from packaging.version import Version


@dataclass
class Package:
    lowest_safe_version: Version | None = None
    lowest_supported_version: Version | None = None
    replacements: Sequence[str] | None = None
