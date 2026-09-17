from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .issues import Pos


@dataclass
class Edit:
    """A replacement of a source range with new text.

    Positions reuse :class:`scrapy_lint.issues.Pos`: ``line`` is 1-based and
    ``column`` is the 0-based UTF-8 byte offset within the line, matching the
    ``col_offset``/``end_col_offset`` produced by :mod:`ast`.
    """

    start: Pos
    end: Pos
    replacement: str


@dataclass
class Fix:
    """An automated correction for an issue, expressed as a set of edits."""

    edits: list[Edit] = field(default_factory=list)
    message: str | None = None


def _line_start_offsets(source: str) -> list[int]:
    """Return the byte offset at which each (1-based) line starts."""
    offsets = [0]
    data = b""
    for line in source.splitlines(keepends=True):
        data += line.encode("utf-8")
        offsets.append(len(data))
    return offsets


def _byte_offset(line_starts: list[int], pos: Pos) -> int:
    return line_starts[pos.line - 1] + pos.column


def source_range(source: str, start: Pos, end: Pos) -> str:
    """Return the text of ``source`` between *start* and *end*."""
    line_starts = _line_start_offsets(source)
    data = source.encode("utf-8")
    return data[
        _byte_offset(line_starts, start) : _byte_offset(line_starts, end)
    ].decode("utf-8")


def apply_edits(source: str, edits: list[Edit]) -> tuple[str, int]:
    """Apply ``edits`` to ``source``, returning the new source and the number
    of edits actually applied.

    Edits are applied from the end of the file backwards so earlier offsets stay
    valid. Any edit that overlaps an already-applied one is skipped, so the
    result is always the largest non-overlapping subset taken back-to-front.
    """
    if not edits:
        return source, 0
    line_starts = _line_start_offsets(source)
    spans = sorted(
        (
            (
                _byte_offset(line_starts, edit.start),
                _byte_offset(line_starts, edit.end),
                edit,
            )
            for edit in edits
        ),
        key=lambda span: span[0],
        reverse=True,
    )
    data = source.encode("utf-8")
    applied = 0
    last_start = len(data)
    for start, end, edit in spans:
        if end > last_start:
            # Overlaps an edit already applied closer to the end of the file.
            continue
        data = data[:start] + edit.replacement.encode("utf-8") + data[end:]
        last_start = start
        applied += 1
    return data.decode("utf-8"), applied
