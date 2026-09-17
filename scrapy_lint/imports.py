from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from scrapy_lint.versions import Versioning

if TYPE_CHECKING:
    from packaging.version import Version

    from scrapy_lint.versions import UnknownUnsupportedVersion


@dataclass
class ImportedObject:
    package: str = "scrapy"
    versioning: Versioning = field(default_factory=Versioning)
    discouraged_in: Version | UnknownUnsupportedVersion | None = None
    replacement: str | None = None
    """Import path to use instead, which is also the fix where the import
    statement can be rewritten to it."""
