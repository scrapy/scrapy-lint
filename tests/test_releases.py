from __future__ import annotations

import json
from datetime import date

import pytest
from packaging.version import Version

from scrapy_lint._releases import (
    _download_releases,
    _parse,
    _releases,
    latest_version,
    outdated,
)

# 2022-01-01 is exactly a year before 2023-01-01, 2021-12-31 is over a year.
VENDORED = "1.0 2021-12-31\n"
DOWNLOADED = "1.1 2022-01-01\n1.2 2023-01-01\n"


@pytest.fixture
def vendored(monkeypatch, tmp_path):
    _vendor(monkeypatch, tmp_path)


@pytest.fixture
def releases(monkeypatch, tmp_path):
    _vendor(monkeypatch, tmp_path)
    monkeypatch.setattr(
        "scrapy_lint._releases._download_releases",
        lambda name: DOWNLOADED,
    )


def _vendor(monkeypatch, tmp_path):
    directory = tmp_path / "vendored"
    directory.mkdir()
    (directory / "fake.txt").write_text(VENDORED, encoding="utf-8")
    monkeypatch.setattr("scrapy_lint._releases._VENDORED_RELEASES", directory)


@pytest.mark.usefixtures("releases")
@pytest.mark.parametrize(
    ("version", "expected"),
    [
        ("1.0", Version("1.2")),
        ("1.1", None),
        ("1.2", None),
        # Unknown versions, e.g. a release newer than the known ones.
        ("9.9", None),
    ],
)
def test_outdated(version, expected):
    assert outdated("fake", Version(version)) == expected


def test_no_release_data(monkeypatch):
    monkeypatch.setattr("scrapy_lint._releases._download_releases", _unreachable)
    assert outdated("fake", Version("1.0")) is None
    assert latest_version("fake") is None


def test_vendored_data():
    latest = latest_version("scrapy")
    assert latest is not None
    assert latest >= Version("2.13.2")


@pytest.mark.usefixtures("releases")
def test_cache(monkeypatch):
    assert latest_version("fake") == Version("1.2")
    _releases.cache_clear()
    monkeypatch.setattr("scrapy_lint._releases._download_releases", _unreachable)
    assert latest_version("fake") == Version("1.2")


@pytest.mark.usefixtures("releases")
def test_stale_cache(monkeypatch, tmp_path):
    assert latest_version("fake") == Version("1.2")
    (tmp_path / "releases" / "fake.txt").touch()
    _releases.cache_clear()
    monkeypatch.setattr("scrapy_lint._releases._MAX_CACHE_AGE", -1)
    monkeypatch.setattr(
        "scrapy_lint._releases._download_releases",
        lambda name: "2.0 2024-01-01",
    )
    assert latest_version("fake") == Version("2.0")


@pytest.mark.usefixtures("releases")
def test_unwritable_cache(monkeypatch, tmp_path):
    unwritable = tmp_path / "file"
    unwritable.touch()
    monkeypatch.setattr(
        "scrapy_lint._releases.user_cache_dir",
        lambda *args: str(unwritable),
    )
    assert latest_version("fake") == Version("1.2")


@pytest.mark.usefixtures("vendored")
def test_failure_delays_the_next_download(tmp_path):
    """A failed download still refreshes the cache file modification time.

    Without it, every run of a project that cannot reach PyPI would wait for
    the download to time out.
    """
    assert latest_version("fake") == Version("1.0")
    assert (tmp_path / "releases" / "fake.txt").exists()


def test_download(monkeypatch):
    data = {
        "releases": {
            "1.0": [
                {"upload_time_iso_8601": "2021-01-02T10:00:00.000000Z"},
                {"upload_time_iso_8601": "2021-01-01T10:00:00.000000Z"},
            ],
            # Pre-releases are not upgrade targets, and versions without files
            # have no release date.
            "1.1rc1": [{"upload_time_iso_8601": "2021-02-01T10:00:00.000000Z"}],
            "1.1": [],
            "not-a-version": [{"upload_time_iso_8601": "2021-03-01T10:00:00.000000Z"}],
        },
    }
    monkeypatch.setattr("scrapy_lint._releases.urlopen", _urlopen(json.dumps(data)))
    # The offline fixture replaces the module attribute, not this reference.
    assert _download_releases("fake") == "1.0 2021-01-01\n"


def test_parse():
    assert _parse("1.0 2021-01-01\nbroken\n1.1 nope\n") == {
        Version("1.0"): date(2021, 1, 1),
    }


def _unreachable(name):
    raise AssertionError(f"unexpected download for {name}")


def _urlopen(text: str):
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return text.encode("utf-8")

    return lambda url, timeout: Response()
