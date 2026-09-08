# /// script
# requires-python = ">=3.10"
# dependencies = ["scrapy-lint"]
#
# [tool.uv.sources]
# scrapy-lint = { path = "../", editable = true }
# ///
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.request import urlopen

from scrapy_lint._stacks import _PYTHON_VERSION, _REQUIREMENTS_URL, _download
from scrapy_lint.requirements import iter_requirement_lines, pinned_version

if TYPE_CHECKING:
    from collections.abc import Generator

TAGS_URL = (
    "https://api.github.com/repos/scrapinghub/scrapinghub-stack-scrapy"
    "/tags?per_page=100&page={page}"
)
STACKS = Path(__file__).parents[1] / "scrapy_lint" / "data" / "stacks"
SUPPORTED_STACK = re.compile(r"2\.\d+-\d{8}")


def iter_tags() -> Generator[str]:
    page = 1
    while True:
        with urlopen(TAGS_URL.format(page=page)) as response:  # noqa: S310
            tags = json.load(response)
        if not tags:
            return
        for tag in tags:
            if SUPPORTED_STACK.fullmatch(tag["name"]):
                yield tag["name"]
        page += 1


def requirements(text: str) -> str:
    python_version = _PYTHON_VERSION.search(text)
    lines = []
    if python_version:
        lines.append(f"# pip-compile with Python {python_version['version']}")
    lines += [
        f"{name}=={version}"
        for _, name, requirement in iter_requirement_lines(text.splitlines())
        if (version := pinned_version(requirement)) is not None
    ]
    return "".join(f"{line}\n" for line in lines)


def main() -> None:
    """Vendor the package list of Scrapy Cloud stacks that are missing."""
    STACKS.mkdir(parents=True, exist_ok=True)
    for tag in iter_tags():
        path = STACKS / f"{tag}.txt"
        if path.exists():
            continue
        path.write_text(
            requirements(_download(_REQUIREMENTS_URL.format(tag=tag))),
            encoding="utf-8",
        )
        print(f"Added {path.relative_to(Path.cwd())}")


if __name__ == "__main__":
    main()
