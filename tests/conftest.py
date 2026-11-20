import pytest

from scrapy_lint._releases import _releases


@pytest.fixture(autouse=True)
def _offline_releases(monkeypatch, tmp_path):
    """Make release data deterministic: vendored data only, no PyPI request."""

    def no_network(name):
        raise OSError(f"network access disabled in tests ({name})")

    monkeypatch.setattr("scrapy_lint._releases._download_releases", no_network)
    monkeypatch.setattr(
        "scrapy_lint._releases.user_cache_dir",
        lambda *args: str(tmp_path),
    )
    _releases.cache_clear()
    yield
    _releases.cache_clear()
