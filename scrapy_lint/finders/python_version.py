from __future__ import annotations

import re
from typing import TYPE_CHECKING

from scrapy_lint._python import allowed_series, end_of_life, pinned_series
from scrapy_lint.issues import EOL_PYTHON, UNFROZEN_PYTHON, Issue, Pos

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

    from scrapy_lint.context import Context, PythonDeclaration


class PythonVersionIssueFinder:  # pylint: disable=too-few-public-methods
    def __init__(self, context: Context):
        self.context = context

    def lint(self, file: Path) -> Generator[Issue]:
        declaration = self.context.project.declared_python
        if declaration is None or declaration.file.resolve() != file:
            return
        pos = key_pos(file, declaration.key)
        yield from self._check_freeze(declaration, pos)
        yield from self._check_end_of_life(declaration, pos)

    def _check_freeze(
        self,
        declaration: PythonDeclaration,
        pos: Pos,
    ) -> Generator[Issue]:
        if pinned_series(declaration.specifier) is not None:
            return
        detail = (
            f"{declaration.key} ({declaration.value}) allows more than one "
            f"Python version"
        )
        yield Issue(UNFROZEN_PYTHON, pos, detail)

    def _check_end_of_life(
        self,
        declaration: PythonDeclaration,
        pos: Pos,
    ) -> Generator[Issue]:
        series = allowed_series(declaration.specifier)
        if not series:
            return
        eol = end_of_life(series[0])
        if eol is None:
            return
        detail = (
            f"{declaration.key} allows Python {series[0]}, which reached its "
            f"end of life on {eol}"
        )
        yield Issue(EOL_PYTHON, pos, detail)


def key_pos(file: Path, key: str) -> Pos:
    """Return the position of the *key* declaration within *file*."""
    pattern = re.compile(rf"^\s*{re.escape(key)}\s*=")
    for number, line in enumerate(
        file.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        if pattern.match(line):
            return Pos(number, len(line) - len(line.lstrip()))
    return Pos()
