from __future__ import annotations

from inspect import cleandoc

from . import NO_ISSUE, Cases, ExpectedIssue, File, cases, iter_issues
from .helpers import check_project


def issue(line: int, column: int) -> ExpectedIssue:
    return ExpectedIssue(
        "SCP52 deprecated method: deprecated in scrapy 2.16.0; "
        "use form2request instead",
        line=line,
        column=column,
        path="a.py",
    )


CASES: Cases = tuple(
    (
        File(cleandoc(code), path="a.py"),
        tuple(iter_issues(issues)),
        {},
    )
    for code, issues in (
        # Every supported way to reach the class.
        (
            """
            from scrapy import FormRequest
            from scrapy.http import FormRequest as AliasedFormRequest
            import scrapy

            FormRequest.from_response(response)
            AliasedFormRequest.from_response(response)
            scrapy.FormRequest.from_response(response)
            scrapy.http.FormRequest.from_response(response)
            """,
            (issue(5, 0), issue(6, 0), issue(7, 0), issue(8, 0)),
        ),
        # Same method name on something else, and the class without the method.
        (
            """
            from scrapy import FormRequest

            Foo.from_response(response)
            from_response(response)
            FormRequest(url)
            """,
            NO_ISSUE,
        ),
        # An alias of a class that is not FormRequest.
        (
            """
            from scrapy import Request as FormRequest2

            FormRequest2.from_response(response)
            """,
            NO_ISSUE,
        ),
    )
)


@cases(CASES)
def test(files, expected, options):
    check_project(files, expected, options)
