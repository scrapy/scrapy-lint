from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from scrapy_lint.versions import Versioning

if TYPE_CHECKING:
    from packaging.version import Version

    from scrapy_lint.versions import UnknownUnsupportedVersion


@dataclass
class API:
    """An API that its package deprecates or removes.

    *path* and *name* are the import path of the API and its name: the callable
    and the parameter for a parameter, the class and the method for a method,
    the module and the member for a module member.

    *discouraged_in* is the version from which the API should be avoided even
    though it still works without a warning, e.g. because its replacement
    already exists, or because there is no replacement and its use was never
    intended. Use :data:`~scrapy_lint.versions.UNKNOWN_UNSUPPORTED_VERSION` for
    APIs that should be avoided in every supported version.

    Where only some values of a parameter are deprecated, list them in
    *deprecated_values*. Set *droppable* if removing a parameter is the right
    way to fix code that passes it once it is gone.
    """

    path: str
    name: str
    versioning: Versioning = field(default_factory=Versioning)
    discouraged_in: Version | UnknownUnsupportedVersion | None = None
    deprecated_values: tuple[Any, ...] | None = None
    droppable: bool = False
    package: str = "scrapy"
