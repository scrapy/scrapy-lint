from __future__ import annotations

import re
from datetime import date
from typing import TYPE_CHECKING

from packaging.version import Version

from scrapy_lint.data.python import PYTHON_EOL, STACK_PYTHON

if TYPE_CHECKING:
    from packaging.specifiers import SpecifierSet

_SERIES_RELEASE_PARTS = 2  # major and minor
_SCRAPY_STACK = re.compile(r"scrapy:(?P<series>[\w.-]+?)(?:-\d{8})?")


def end_of_life(series: str) -> date | None:
    """Return the end-of-life date of the *series* Python series.

    The result is ``None`` for series that are still supported, and for series
    with no known end-of-life date.
    """
    eol = PYTHON_EOL.get(series)
    if eol is None or eol > date.today():
        return None
    return eol


def allowed_series(specifier: SpecifierSet) -> list[str]:
    """Return the known Python series that *specifier* allows, oldest first."""
    series = pinned_series(specifier)
    if series is not None:
        return [series]
    # PYTHON_EOL goes from the oldest series to the newest one.
    return [series for series in PYTHON_EOL if specifier.contains(series)]


def pinned_series(specifier: SpecifierSet) -> str | None:
    """Return the Python series that *specifier* pins.

    The result is ``None`` for specifiers that allow more than one series, e.g.
    version ranges.
    """
    if len(specifier) != 1:
        return None
    spec = next(iter(specifier))
    if spec.operator not in {"==", "~="}:
        return None
    version = Version(spec.version.removesuffix(".*"))
    if spec.operator == "~=" and len(version.release) <= _SERIES_RELEASE_PARTS:
        return None
    return f"{version.major}.{version.minor}"


def stack_python(stack: str) -> str | None:
    """Return the Python series that the *stack* Scrapy Cloud stack runs.

    The result is ``None`` for stacks that are not known Scrapy stacks.
    """
    match = _SCRAPY_STACK.fullmatch(stack)
    return STACK_PYTHON.get(match["series"]) if match else None
