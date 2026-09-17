# /// script
# requires-python = ">=3.10"
# dependencies = ["scrapy-lint"]
#
# [tool.uv.sources]
# scrapy-lint = { path = "../", editable = true }
# ///
from pathlib import Path

from scrapy_lint._releases import _VENDORED_RELEASES, _download_releases

PACKAGES = ("scrapy",)


def main() -> None:
    """Vendor the release dates of the packages that have a release policy."""
    _VENDORED_RELEASES.mkdir(parents=True, exist_ok=True)
    for name in PACKAGES:
        path = _VENDORED_RELEASES / f"{name}.txt"
        path.write_text(_download_releases(name), encoding="utf-8")
        print(f"Updated {path.relative_to(Path.cwd())}")


if __name__ == "__main__":
    main()
