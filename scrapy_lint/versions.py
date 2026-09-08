from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from packaging.version import Version


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
