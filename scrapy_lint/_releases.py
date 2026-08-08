from __future__ import annotations

from datetime import date, timedelta
from functools import lru_cache
from json import loads
from pathlib import Path
from time import time
from urllib.request import urlopen

from packaging.version import Version
from platformdirs import user_cache_dir

_DEPRECATION_WINDOW = timedelta(days=365)
_DOWNLOAD_TIMEOUT = 5
_MAX_CACHE_AGE = timedelta(days=7).total_seconds()
_PYPI_URL = "https://pypi.org/pypi/{name}/json"
_VENDORED_RELEASES = Path(__file__).parent / "data" / "releases"


def outdated(name: str, version: Version) -> Version | None:
    """Return the latest release of *name* if *version* is over a year older.

    The result is ``None`` for packages without release data, for unknown
    versions, and for versions released within a year of the latest release.
    """
    releases = _releases(name)
    if not releases:
        return None
    released = releases.get(version)
    latest = max(releases)
    if released is None or releases[latest] - released <= _DEPRECATION_WINDOW:
        return None
    return latest


def latest_version(name: str) -> Version | None:
    """Return the latest known release of *name*, ``None`` without release data."""
    releases = _releases(name)
    return max(releases) if releases else None


@lru_cache
def _releases(name: str) -> dict[Version, date]:
    """Return the release date of every known release of *name*.

    Dates come from the data vendored into scrapy-lint, extended with a weekly
    cache of the release history that PyPI reports. Packages without vendored
    data are unknown, and never downloaded.
    """
    vendored = _read(_VENDORED_RELEASES / f"{name}.txt")
    if not vendored:
        return {}
    releases = _parse(vendored)
    releases.update(_parse(_cached_text(name)))
    return releases


def _cached_text(name: str) -> str:
    path = Path(user_cache_dir("scrapy-lint")) / "releases" / f"{name}.txt"
    if _age(path) <= _MAX_CACHE_AGE:
        return _read(path)
    try:
        text = _download_releases(name)
    except (OSError, ValueError, KeyError):
        # Refresh the modification time of the cache file, creating it empty if
        # needed, so that a failure does not make every run pay the timeout.
        text = _read(path)
        _write(path, text)
        return text
    _write(path, text)
    return text


def _age(path: Path) -> float:
    try:
        return time() - path.stat().st_mtime
    except OSError:
        return float("inf")


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _write(path: Path, text: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    except OSError:
        pass


def _parse(text: str) -> dict[Version, date]:
    releases = {}
    for line in text.splitlines():
        version, _, released = line.partition(" ")
        try:
            releases[Version(version)] = date.fromisoformat(released)
        except ValueError:
            continue
    return releases


def _download_releases(name: str) -> str:
    """Return the release dates of *name* on PyPI, as ``version date`` lines."""
    with urlopen(  # noqa: S310
        _PYPI_URL.format(name=name),
        timeout=_DOWNLOAD_TIMEOUT,
    ) as response:
        data = loads(response.read())
    releases = {}
    for version, files in data["releases"].items():
        try:
            parsed = Version(version)
        except ValueError:
            continue
        if parsed.is_prerelease or not files:
            continue
        releases[parsed] = min(file["upload_time_iso_8601"][:10] for file in files)
    return "".join(f"{version} {releases[version]}\n" for version in sorted(releases))
