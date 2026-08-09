from __future__ import annotations

from . import NO_ISSUE, Cases, ExpectedIssue, File, cases, iter_issues
from .helpers import check_project
from .test_requirements import SCRAPY_HIGHEST_KNOWN

CASES: Cases = tuple(
    (
        (
            File(
                "\n".join((f"scrapy=={SCRAPY_HIGHEST_KNOWN}", *requirements)),
                path="requirements.txt",
            ),
            File(code, path="a.py"),
        ),
        (
            ExpectedIssue(
                "SCP13 incomplete requirements freeze",
                path="requirements.txt",
            ),
            *iter_issues(issues),
        ),
        {},
    )
    for requirements, code, issues in (
        # The version of the package that provides the injectable determines
        # whether or not its use is reported.
        (
            ("scrapy-poet==0.14.0",),
            "from web_poet import Stats",
            ExpectedIssue(
                "SCP53 unsupported injectable: added in scrapy-poet 0.15.0",
                path="a.py",
                column=21,
            ),
        ),
        (("scrapy-poet==0.15.0",), "from web_poet import Stats", NO_ISSUE),
        (("scrapy-poet",), "from web_poet import Stats", NO_ISSUE),
        ((), "from web_poet import Stats", NO_ISSUE),
        # Injectables can be imported from any web-poet module, aliased, or
        # used through an attribute chain.
        (
            ("scrapy-poet==0.14.0",),
            "from web_poet.page_inputs.stats import Stats as PoetStats",
            ExpectedIssue(
                "SCP53 unsupported injectable: added in scrapy-poet 0.15.0",
                path="a.py",
                column=48,
            ),
        ),
        (
            ("scrapy-poet==0.16.0",),
            "import web_poet\n\ndef parse(request: web_poet.HttpRequest): pass",
            ExpectedIssue(
                "SCP53 unsupported injectable: added in scrapy-poet 0.17.0",
                path="a.py",
                line=3,
                column=19,
            ),
        ),
        # Objects that are not injectables, and injectables from other
        # packages, are ignored.
        (("scrapy-poet==0.14.0",), "from web_poet import WebPage", NO_ISSUE),
        (("scrapy-poet==0.14.0",), "from foo import Stats", NO_ISSUE),
        (("scrapy-poet==0.14.0",), "import foo\nfoo.Stats", NO_ISSUE),
    )
)


@cases(CASES)
def test(files, expected, options):
    check_project(files, expected, options)
