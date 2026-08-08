import ast
from ast import AST, Assign, ClassDef, Constant, JoinedStr, List, Name, Tuple
from collections.abc import Generator

from scrapy_lint.fixes import Edit, Fix
from scrapy_lint.issues import START_URL, Issue, Pos


class StartUrlIssueFinder:
    def __init__(self, source: str | None = None):
        self.source = source

    def __call__(self, node: AST) -> Generator[Issue]:
        assert isinstance(node, ClassDef)
        assignments = {
            statement.targets[0].id: statement
            for statement in node.body
            if isinstance(statement, Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], Name)
        }
        if "start_urls" in assignments or "start_url" not in assignments:
            return
        statement = assignments["start_url"]
        yield Issue(
            START_URL,
            Pos.from_node(statement.targets[0]),
            fix=self.build_fix(statement),
        )

    def build_fix(self, statement: Assign) -> Fix | None:
        """Build a fix that rewrites the assignment as a *start_urls* one,
        wrapping the value in a list unless it is already a sequence.

        Returns ``None`` (report only, no fix) when the value is neither a
        string nor a sequence literal, and hence there is no way to tell
        whether it needs wrapping.
        """
        if self.source is None:
            return None
        value = statement.value
        if isinstance(value, JoinedStr) or (
            isinstance(value, Constant) and isinstance(value.value, str)
        ):
            template = "start_urls = [{}]"
        elif isinstance(value, (List, Tuple)):
            template = "start_urls = {}"
        else:
            return None
        segment = ast.get_source_segment(self.source, value)
        assert segment is not None
        replacement = template.format(segment)
        assert value.end_lineno is not None
        assert value.end_col_offset is not None
        edit = Edit(
            start=Pos.from_node(statement.targets[0]),
            end=Pos(value.end_lineno, value.end_col_offset),
            replacement=replacement,
        )
        return Fix([edit], message="rename start_url to start_urls")
