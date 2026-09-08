from __future__ import annotations

from . import NO_ISSUE, Cases, ExpectedIssue, File, cases, iter_issues
from .helpers import check_project

PATH = "a.py"
REQUIREMENTS = "requirements.txt"
SPIDER = """\
from __future__ import annotations

from typing import TYPE_CHECKING

import scrapy

if TYPE_CHECKING:
    from scrapy.http import Response


class MySpider(scrapy.Spider):
    name = "my"

    def parse(self, response: Response):
        pass
"""
ISSUE = ExpectedIssue(
    message="SCP47 hidden callback type hint: Response",
    line=14,
    column=30,
    path=PATH,
)
PARTIAL_FREEZE = ExpectedIssue(
    message="SCP13 incomplete requirements freeze",
    path=REQUIREMENTS,
)
CASES: Cases = (
    *(
        (
            (File(requirements, path=REQUIREMENTS), File(code, path=PATH)),
            [PARTIAL_FREEZE, *iter_issues(issues)],
            {},
        )
        for requirements, code, issues in (
            # Requirements gating
            *(
                (requirements, SPIDER, issues)
                for requirements, issues in (
                    ("scrapy-poet==0.28.0", ISSUE),
                    # scrapy-poet is an extra of scrapy-zyte-api
                    ("scrapy-zyte-api==0.36.0", NO_ISSUE),
                )
            ),
            # Only run-time annotations break
            *(
                ("scrapy-poet==0.28.0", code, NO_ISSUE)
                for code in (
                    # Eagerly-evaluated annotations fail on import instead
                    SPIDER.replace("from __future__ import annotations\n\n", ""),
                    # Imported for run time
                    SPIDER.replace("if TYPE_CHECKING:\n    ", ""),
                    SPIDER.replace(
                        "if TYPE_CHECKING:\n    from scrapy.http import Response",
                        "if TYPE_CHECKING:\n    pass\nelse:\n"
                        "    from scrapy.http import Response",
                    ),
                    # Not a spider
                    SPIDER.replace("scrapy.Spider", "object"),
                    # Not an annotation
                    SPIDER.replace(": Response", ""),
                )
            ),
            # Return annotations are resolved as well
            (
                "scrapy-poet==0.28.0",
                SPIDER.replace("response: Response)", "response) -> Response"),
                ISSUE.replace(column=33),
            ),
            # Every hidden name of an annotation is reported
            (
                "scrapy-poet==0.28.0",
                SPIDER.replace(
                    "from scrapy.http import Response",
                    "from scrapy.http import Response, TextResponse",
                ).replace(": Response", ": Response | TextResponse"),
                (
                    ISSUE,
                    ISSUE.replace(
                        message="SCP47 hidden callback type hint: TextResponse",
                        column=41,
                    ),
                ),
            ),
        )
    ),
    # Without requirements, the rule cannot know if injection is in use
    ((File(SPIDER, path=PATH),), NO_ISSUE, {}),
)


@cases(CASES)
def test(
    files: File | list[File],
    expected: ExpectedIssue | list[ExpectedIssue] | None,
    options,
):
    check_project(files, expected, options)
