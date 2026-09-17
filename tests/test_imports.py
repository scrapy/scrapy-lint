from __future__ import annotations

import ast
from pathlib import Path

from scrapy_lint.context import Project
from scrapy_lint.finders.imports import ImportIssueFinder
from tests.helpers import check_project

from . import (
    NO_ISSUE,
    Cases,
    ExpectedIssue,
    File,
    cases,
    insecure_scrapy_issues,
    iter_issues,
)

PATH = "a.py"
CASES: Cases = (
    *(
        (
            (
                File("", path="scrapy.cfg"),
                File(requirements, path="requirements.txt"),
                File(code, path=PATH),
            ),
            (
                ExpectedIssue(
                    "SCP13 incomplete requirements freeze",
                    path="requirements.txt",
                ),
                *insecure_scrapy_issues(requirements),
                *iter_issues(issues),  # type: ignore[arg-type]
            ),
            {},
        )
        for requirements, code, issues in (
            # SCP49 deprecated import
            (
                "scrapy==2.17.0",
                "from scrapy.utils.ssl import x509name_to_string",
                ExpectedIssue(
                    "SCP49 deprecated import: deprecated in scrapy 2.17.0",
                    column=29,
                    path=PATH,
                ),
            ),
            (
                "scrapy==2.17.0",
                "from scrapy.utils.ssl import x509name_to_string as to_string",
                ExpectedIssue(
                    "SCP49 deprecated import: deprecated in scrapy 2.17.0",
                    column=51,
                    path=PATH,
                ),
            ),
            (
                "scrapy==2.17.0",
                "from scrapy.core.downloader.tls import METHOD_TLS, DEFAULT_CIPHERS",
                tuple(
                    ExpectedIssue(
                        "SCP49 deprecated import: deprecated in scrapy 2.17.0",
                        column=column,
                        path=PATH,
                    )
                    for column in (39, 51)
                ),
            ),
            # SCP77 discouraged API: not deprecated yet, but never meant to
            # be imported
            (
                "scrapy==2.16.0",
                "from scrapy.utils.ssl import x509name_to_string",
                ExpectedIssue(
                    "SCP77 discouraged API: to be deprecated in scrapy 2.17.0",
                    column=29,
                    path=PATH,
                ),
            ),
            # SCP50 removed import, with the replacement as guidance
            (
                "scrapy==2.16.0",
                "from scrapy.utils.url import canonicalize_url",
                ExpectedIssue(
                    "SCP50 removed import: deprecated in scrapy 2.13.0, removed "
                    "in 2.16.0; use w3lib.url.canonicalize_url instead",
                    column=29,
                    path=PATH,
                ),
            ),
            (
                "scrapy==2.15.0",
                "from scrapy.utils.url import canonicalize_url",
                ExpectedIssue(
                    "SCP49 deprecated import: deprecated in scrapy 2.13.0; use "
                    "w3lib.url.canonicalize_url instead",
                    column=29,
                    path=PATH,
                ),
            ),
            # SCP50 removed import: an entry for a module covers its objects,
            # however they are imported
            (
                "scrapy==2.16.0",
                "from scrapy.spiders.init import InitSpider",
                ExpectedIssue(
                    "SCP50 removed import: deprecated in scrapy 2.13.0, removed "
                    "in 2.16.0",
                    column=32,
                    path=PATH,
                ),
            ),
            (
                "scrapy==2.16.0",
                "import scrapy.utils.testproc",
                ExpectedIssue(
                    "SCP50 removed import: deprecated in scrapy 2.13.0, removed "
                    "in 2.16.0",
                    column=7,
                    path=PATH,
                ),
            ),
            # SCP49 deprecated import: no version in requirements.txt
            (
                "scrapy",
                "from scrapy.utils.ssl import x509name_to_string",
                NO_ISSUE,
            ),
            # SCP49 deprecated import: neither the module nor its remaining
            # objects are deprecated
            *(
                ("scrapy==2.17.0", code, NO_ISSUE)
                for code in (
                    "import scrapy.utils.ssl",
                    "from scrapy.utils.ssl import ffi_buf_to_bytes",
                    "from . import ssl",
                )
            ),
        )
    ),
)


@cases(CASES)
def test(files, expected, options):
    check_project(files, expected, options)


def test_build_fix_without_source():
    finder = ImportIssueFinder(Project(Path.cwd()))
    node = ast.parse("from scrapy.utils.url import canonicalize_url").body[0]
    assert finder.build_fix(node) is None
