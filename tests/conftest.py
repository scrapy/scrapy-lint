from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from scrapy_lint import _stacks

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def stack_cache(tmp_path: Path) -> Path:
    return tmp_path / "cache"


@pytest.fixture(autouse=True)
def offline(monkeypatch: pytest.MonkeyPatch, stack_cache: Path) -> None:
    """Keep tests away from the user cache, the network and uv."""

    def download(url: str) -> str:
        raise OSError(url)

    monkeypatch.setattr(_stacks, "user_cache_dir", lambda *_: str(stack_cache))
    monkeypatch.setattr(_stacks, "_download", download)
    monkeypatch.setattr(_stacks, "which", lambda _: None)
