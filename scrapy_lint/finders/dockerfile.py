from __future__ import annotations

import re
from typing import TYPE_CHECKING

from scrapy_lint.issues import STACK_NOT_FROZEN, Issue, Pos

if TYPE_CHECKING:
    from collections.abc import Generator

    from scrapy_lint.context import Context


def find_dockerfile_issues(context: Context) -> Generator[Issue]:
    for line, column, tag in context.project.dockerfile_stacks:
        if not re.search(r"-\d{8}$", tag):
            yield Issue(STACK_NOT_FROZEN, Pos(line, column))
