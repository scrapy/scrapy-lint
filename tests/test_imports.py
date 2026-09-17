from __future__ import annotations

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
            (
                "scrapy==2.18.0",
                "from scrapy.utils.python import re_rsearch",
                ExpectedIssue(
                    "SCP49 deprecated import: deprecated in scrapy 2.18.0",
                    column=32,
                    path=PATH,
                ),
            ),
            # SCP49 deprecated import: module entry, covering every object in
            # the module
            (
                "scrapy==2.18.0",
                "from scrapy.interfaces import ISpiderLoader",
                ExpectedIssue(
                    "SCP49 deprecated import: deprecated in scrapy 2.18.0; follow "
                    "scrapy.spiderloader.SpiderLoaderProtocol instead",
                    column=30,
                    path=PATH,
                ),
            ),
            # SCP50 removed import
            (
                "scrapy==2.18.0",
                "from scrapy.utils.iterators import xmliter",
                ExpectedIssue(
                    "SCP50 removed import: deprecated in scrapy 2.11.1, removed in "
                    "2.18.0; use xmliter_lxml instead",
                    column=35,
                    path=PATH,
                ),
            ),
            (
                "scrapy==2.17.0",
                "from scrapy.utils.iterators import xmliter",
                ExpectedIssue(
                    "SCP49 deprecated import: deprecated in scrapy 2.11.1; use "
                    "xmliter_lxml instead",
                    column=35,
                    path=PATH,
                ),
            ),
            # SCP50 removed import: no sunset guidance
            (
                "scrapy==2.18.0",
                "from scrapy.utils.misc import md5sum",
                ExpectedIssue(
                    "SCP50 removed import: deprecated in scrapy 2.12.0, removed in "
                    "2.18.0",
                    column=30,
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
