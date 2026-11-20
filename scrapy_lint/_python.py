from __future__ import annotations

import re
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING

from packaging.version import Version

from scrapy_lint.data.python import PYTHON_EOL, STACK_PYTHON

if TYPE_CHECKING:
    from packaging.specifiers import SpecifierSet

_SERIES_RELEASE_PARTS = 2  # major and minor
_SCRAPY_STACK = re.compile(r"scrapy:(?P<series>[\w.-]+?)(?:-\d{8})?")
# Micro versions probed to find out whether a specifier allows a series. A
# specifier may exclude the first releases of a series, e.g. ">=3.11.5,<3.12".
_SERIES_PROBE_MICROS = (0, 99)
# Version beyond every series that Python may realistically ever reach. A
# specifier that allows it is open-ended, and hence allows series that are not
# known yet.
_FUTURE_VERSION = "9999.0"


def end_of_life(series: str) -> date | None:
    """Return the end-of-life date of the *series* Python series.

    The result is ``None`` for series that are still supported, and for series
    with no known end-of-life date.
    """
    eol = PYTHON_EOL.get(series)
    if eol is None or eol > datetime.now(tz=timezone.utc).date():
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
    open version ranges.
    """
    series = _named_series(specifier)
    if series is not None:
        return series
    return _sole_allowed_series(specifier)


def _named_series(specifier: SpecifierSet) -> str | None:
    """Return the Python series that a lone ``==`` or ``~=`` specifier names."""
    if len(specifier) != 1:
        return None
    spec = next(iter(specifier))
    if spec.operator not in {"==", "~="}:
        return None
    version = Version(spec.version.removesuffix(".*"))
    if spec.operator == "~=" and len(version.release) <= _SERIES_RELEASE_PARTS:
        return None
    return f"{version.major}.{version.minor}"


def _sole_allowed_series(specifier: SpecifierSet) -> str | None:
    """Return the only known Python series that *specifier* allows.

    The result is ``None`` unless *specifier* is bounded above, since an
    open-ended range also allows series that are not known yet, and ``None``
    as well when the known series that it allows are not exactly one, e.g. for
    ``">=3.12"`` or ``">=3.99,<4.0"``.
    """
    if specifier.contains(_FUTURE_VERSION):
        return None
    allowed = [series for series in PYTHON_EOL if _allows_series(specifier, series)]
    if len(allowed) != 1:
        return None
    return allowed[0]


def _allows_series(specifier: SpecifierSet, series: str) -> bool:
    return any(
        specifier.contains(f"{series}.{micro}") for micro in _SERIES_PROBE_MICROS
    )


def stack_python(stack: str) -> str | None:
    """Return the Python series that the *stack* Scrapy Cloud stack runs.

    The result is ``None`` for stacks that are not known Scrapy stacks.
    """
    match = _SCRAPY_STACK.fullmatch(stack)
    return STACK_PYTHON.get(match["series"]) if match else None
