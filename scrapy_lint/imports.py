from __future__ import annotations

from dataclasses import dataclass, field

from scrapy_lint.versions import Versioning


@dataclass
class ImportedObject:
    package: str = "scrapy"
    versioning: Versioning = field(default_factory=Versioning)
