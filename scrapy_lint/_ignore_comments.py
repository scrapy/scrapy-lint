from __future__ import annotations

import re
import tokenize
from dataclasses import dataclass, field
from io import StringIO
from typing import TYPE_CHECKING

from .fixes import Edit
from .issues import Pos

if TYPE_CHECKING:
    from collections.abc import Iterable

    from .issues import Issue

_IGNORE_COMMENT = re.compile(
    r"#\s*scrapy-lint:\s*ignore(?P<codes>\[[^]]*\])?",
    re.IGNORECASE,
)
_IGNORE_COMMENT_CODE = re.compile(r"SCP(\d+)", re.IGNORECASE)
_DOCKERFILE_DIRECTIVE = re.compile(r"\s*#\s*(?P<name>\w+)\s*=\s*(?P<value>\S+)")


def _codes(match: re.Match[str]) -> set[int] | None:
    codes = match["codes"]
    if codes is None:
        return None
    return {int(code) for code in _IGNORE_COMMENT_CODE.findall(codes)}


def _byte_column(text: str, index: int) -> int:
    return len(text[:index].encode("utf-8"))


def _is_comment_or_blank(line: str) -> bool:
    stripped = line.strip()
    return not stripped or stripped.startswith("#")


def _forward_anchors(line_count: int, commentable: set[int]) -> dict[int, int]:
    """Map every line that cannot take a trailing comment to the next line
    that can."""
    anchors = {}
    pending: list[int] = []
    for number in range(1, line_count + 1):
        if number not in commentable:
            pending.append(number)
            continue
        for line in pending:
            anchors[line] = number
        pending = []
    return anchors


@dataclass
class IgnoreComments:
    """The ignore comments of a file, and where new ones can go.

    Every line maps to an anchor line, the line whose ignore comment covers it.
    When *preceding* is true, that comment is on its own line right before the
    anchor line. Otherwise, it is at the end of the anchor line.
    """

    lines: list[str]
    preceding: bool = False
    anchors: dict[int, int] = field(default_factory=dict)
    comments: dict[int, re.Match[str]] = field(default_factory=dict)
    """Ignore comment of each anchor line that has one."""

    def anchor(self, line: int) -> int:
        return self.anchors.get(line, line)

    def ignores(self, issue: Issue) -> bool:
        match = self.comments.get(self.anchor(issue.line))
        if match is None:
            return False
        codes = _codes(match)
        return codes is None or issue.code in codes

    def edits(self, issues: Iterable[Issue]) -> list[Edit]:
        """Return the edits that make ignore comments cover *issues*."""
        codes_by_anchor: dict[int, set[int]] = {}
        for issue in issues:
            codes_by_anchor.setdefault(self.anchor(issue.line), set()).add(
                issue.code,
            )
        return [self._edit(anchor, codes) for anchor, codes in codes_by_anchor.items()]

    def _edit(self, anchor: int, codes: set[int]) -> Edit:
        match = self.comments.get(anchor)
        if match is not None:
            codes |= _codes(match) or set()
            line = anchor - 1 if self.preceding else anchor
            start, end = (
                match.span("codes") if match["codes"] else (match.end(), match.end())
            )
            return Edit(
                Pos(line, _byte_column(match.string, start)),
                Pos(line, _byte_column(match.string, end)),
                _brackets(codes),
            )
        text = self.lines[anchor - 1]
        comment = f"# scrapy-lint: ignore{_brackets(codes)}"
        if self.preceding:
            indent = text[: len(text) - len(text.lstrip())]
            return Edit(Pos(anchor, 0), Pos(anchor, 0), f"{indent}{comment}\n")
        content = text.rstrip()
        return Edit(
            Pos(anchor, _byte_column(content, len(content))),
            Pos(anchor, _byte_column(text, len(text))),
            f"  {comment}",
        )


def _brackets(codes: set[int]) -> str:
    return "[" + ", ".join(f"SCP{code:02}" for code in sorted(codes)) + "]"


def python_ignore_comments(source: str) -> IgnoreComments:
    """Return the ignore comments of Python *source*.

    Lines inside a multi-line string or ending in a backslash continuation
    are covered by the comment at the end of the next line that can take one,
    the way Ruff handles ``noqa`` comments.
    """
    lines = source.split("\n")
    commentable = set()
    comments = {}
    for token in tokenize.generate_tokens(StringIO(source).readline):
        if token.type not in {tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE}:
            continue
        line, column = token.start
        commentable.add(line)
        if token.type == tokenize.COMMENT:
            match = _IGNORE_COMMENT.search(lines[line - 1], column)
            if match:
                comments[line] = match
    return IgnoreComments(
        lines,
        anchors=_forward_anchors(len(lines), commentable),
        comments=comments,
    )


def trailing_ignore_comments(source: str) -> IgnoreComments:
    """Return the ignore comments of *source*, a file where comments can go at
    the end of any line."""
    lines = source.split("\n")
    comments = {}
    for number, line in enumerate(lines, start=1):
        match = _IGNORE_COMMENT.search(line)
        if match:
            comments[number] = match
    return IgnoreComments(lines, comments=comments)


def _dockerfile_escape(lines: list[str]) -> str:
    for line in lines:
        match = _DOCKERFILE_DIRECTIVE.match(line)
        if not match:
            break
        if match["name"].lower() == "escape":
            return match["value"]
    return "\\"


def preceding_ignore_comments(
    source: str,
    *,
    dockerfile: bool = False,
) -> IgnoreComments:
    """Return the ignore comments of *source*, a file where comments can only
    take a whole line, and cover the line that follows them.

    If *dockerfile* is true, a comment covers every line of the Dockerfile
    instruction that follows it.
    """
    lines = source.split("\n")
    escape = _dockerfile_escape(lines) if dockerfile else None
    anchors = {}
    comments = {}
    start = None
    for number, line in enumerate(lines, start=1):
        if start is None:
            if _is_comment_or_blank(line):
                continue
            start = number
            previous = lines[number - 2] if number > 1 else ""
            if previous.lstrip().startswith("#") and (
                match := _IGNORE_COMMENT.search(previous)
            ):
                comments[number] = match
        anchors[number] = start
        if _is_comment_or_blank(line):
            continue
        if escape is None or not line.rstrip().endswith(escape):
            start = None
    return IgnoreComments(lines, preceding=True, anchors=anchors, comments=comments)
