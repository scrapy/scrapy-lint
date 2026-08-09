from __future__ import annotations

import ast
import tokenize
from ast import AST, AnnAssign, Assign, ClassDef, Constant, Expr
from functools import cached_property
from io import StringIO
from typing import TYPE_CHECKING

from scrapy_lint.fixes import Edit, Fix
from scrapy_lint.issues import DOCUMENTATION_COMMENT, Issue, Pos

if TYPE_CHECKING:
    from collections.abc import Generator, Sequence

ITEM_BASES = frozenset({"BaseModel", "DictItem", "Item"})
ITEM_DECORATORS = frozenset({"attrs", "dataclass", "define", "frozen", "mutable", "s"})


def get_name(node: AST) -> str | None:
    """Return the last component of a dotted name, e.g. ``Item`` for both
    ``Item`` and ``scrapy.Item``."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def is_item_class(node: ClassDef) -> bool:
    """Return whether *node* defines an item class of any of the kinds that
    itemadapter supports."""
    if any(get_name(base) in ITEM_BASES for base in node.bases):
        return True
    return any(
        get_name(decorator.func if isinstance(decorator, ast.Call) else decorator)
        in ITEM_DECORATORS
        for decorator in node.decorator_list
    )


def build_docstring(texts: Sequence[str], indent: str) -> str | None:
    """Return a docstring holding *texts*, one per line, indented with
    *indent*, or ``None`` if the text cannot be quoted as one."""
    body = f"\n{indent}".join(texts)
    if '"""' in body or body.endswith(('"', "\\")):
        return None
    return f'"""{body}"""'


class DocumentationCommentIssueFinder:
    def __init__(self, source: str):
        self.source = source

    @cached_property
    def lines(self) -> list[str]:
        return self.source.splitlines()

    @cached_property
    def comments(self) -> dict[int, tokenize.TokenInfo]:
        """Documentation comments, i.e. comments starting with ``#:``, by line
        number."""
        tokens = tokenize.generate_tokens(StringIO(self.source).readline)
        return {
            token.start[0]: token
            for token in tokens
            if token.type == tokenize.COMMENT and token.string.startswith("#:")
        }

    def __call__(self, node: AST) -> Generator[Issue]:
        if not isinstance(node, ClassDef) or not self.comments:
            return
        if not is_item_class(node):
            return
        for index, statement in enumerate(node.body):
            if not isinstance(statement, (Assign, AnnAssign)):
                continue
            yield from self.find_leading_issues(node.body, index, statement)
            yield from self.find_trailing_issues(statement)

    def find_leading_issues(
        self,
        body: list[ast.stmt],
        index: int,
        statement: Assign | AnnAssign,
    ) -> Generator[Issue]:
        tokens = []
        line = statement.lineno - 1
        while (token := self.comments.get(line)) and self.is_standalone(token):
            tokens.append(token)
            line -= 1
        if not tokens:
            return
        tokens.reverse()
        pos = Pos(tokens[0].start[0], tokens[0].start[1])
        yield Issue(
            DOCUMENTATION_COMMENT,
            pos,
            fix=self.build_fix(body, index, statement, tokens),
        )

    def find_trailing_issues(self, statement: Assign | AnnAssign) -> Generator[Issue]:
        assert statement.end_lineno is not None
        token = self.comments.get(statement.end_lineno)
        if token is None or self.is_standalone(token):
            return
        yield Issue(DOCUMENTATION_COMMENT, Pos(token.start[0], token.start[1]))

    def build_fix(
        self,
        body: list[ast.stmt],
        index: int,
        statement: Assign | AnnAssign,
        tokens: list[tokenize.TokenInfo],
    ) -> Fix | None:
        """Build a fix that turns a leading documentation comment block into a
        docstring below the documented assignment.

        Returns ``None`` (report only, no fix) when the assignment already has
        a docstring or when the comment text cannot be quoted as one.
        """
        following = body[index + 1] if index + 1 < len(body) else None
        if (
            isinstance(following, Expr)
            and isinstance(following.value, Constant)
            and isinstance(following.value.value, str)
        ):
            return None
        assert statement.end_lineno is not None
        indent = self.lines[statement.lineno - 1][: statement.col_offset]
        docstring = build_docstring(
            [token.string[2:].strip() for token in tokens],
            indent,
        )
        if docstring is None:
            return None
        code = "\n".join(self.lines[statement.lineno - 1 : statement.end_lineno])
        end_column = len(self.lines[statement.end_lineno - 1].encode("utf-8"))
        edit = Edit(
            start=Pos(tokens[0].start[0], 0),
            end=Pos(statement.end_lineno, end_column),
            replacement=f"{code}\n{indent}{docstring}",
        )
        return Fix([edit], message="replace documentation comment with docstring")

    @staticmethod
    def is_standalone(token: tokenize.TokenInfo) -> bool:
        return not token.line[: token.start[1]].strip()
