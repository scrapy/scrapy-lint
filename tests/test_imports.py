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
            (
                "scrapy==2.15.0",
                "from scrapy.mail import MailSender",
                ExpectedIssue(
                    "SCP49 deprecated import: deprecated in scrapy 2.15.0; use "
                    "smtplib, twisted.mail.smtp or a third-party email library "
                    "instead",
                    column=24,
                    path=PATH,
                ),
            ),
            (
                "scrapy==2.15.0",
                "from scrapy.extensions.statsmailer import StatsMailer",
                ExpectedIssue(
                    "SCP49 deprecated import: deprecated in scrapy 2.15.0; handle "
                    "the spider_closed signal to send your own notifications instead",
                    column=42,
                    path=PATH,
                ),
            ),
            (
                "scrapy==2.16.0",
                "from scrapy.utils.python import MutableChain",
                ExpectedIssue(
                    "SCP49 deprecated import: deprecated in scrapy 2.16.0",
                    column=32,
                    path=PATH,
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
            (
                "scrapy==2.13.0",
                "from scrapy.core.downloader.handlers.http import HTTPDownloadHandler",
                ExpectedIssue(
                    "SCP77 discouraged API: to be deprecated in scrapy 2.14.0; "
                    "import HTTP11DownloadHandler from "
                    "scrapy.core.downloader.handlers.http11 instead",
                    column=49,
                    path=PATH,
                ),
            ),
            # SCP49 deprecated import: sunset guidance
            (
                "scrapy==2.15.0",
                "from scrapy.utils.misc import walk_modules",
                ExpectedIssue(
                    "SCP49 deprecated import: deprecated in scrapy 2.15.0; "
                    "use walk_modules_iter() instead",
                    column=30,
                    path=PATH,
                ),
            ),
            # SCP49 deprecated import: the replacement does not exist yet
            (
                "scrapy==2.14.0",
                "from scrapy.utils.misc import walk_modules",
                NO_ISSUE,
            ),
            # SCP49 deprecated import: deprecation reverted in a later version
            (
                "scrapy==2.16.0",
                "from scrapy import FormRequest",
                ExpectedIssue(
                    "SCP49 deprecated import: deprecated in scrapy 2.16.0; "
                    "use the form2request library instead",
                    column=19,
                    path=PATH,
                ),
            ),
            *(
                (requirements, "from scrapy import FormRequest", NO_ISSUE)
                for requirements in ("scrapy==2.15.0", "scrapy==2.17.0")
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
            # SCP49 deprecated import: version ranges
            (
                "scrapy",
                "from scrapy.utils.ssl import x509name_to_string",
                ExpectedIssue(
                    "SCP49 deprecated import: deprecated in scrapy 2.17.0; this "
                    "project supports any scrapy version",
                    column=29,
                    path=PATH,
                ),
            ),
            (
                "scrapy>=2.16.0",
                "from scrapy.utils.ssl import x509name_to_string",
                ExpectedIssue(
                    "SCP49 deprecated import: deprecated in scrapy 2.17.0; this "
                    "project supports scrapy >=2.16.0",
                    column=29,
                    path=PATH,
                ),
            ),
            (
                "scrapy>=2.15.0,<2.17.0",
                "from scrapy.utils.ssl import x509name_to_string",
                ExpectedIssue(
                    "SCP77 discouraged API: to be deprecated in scrapy 2.17.0; "
                    "this project supports scrapy >=2.15.0,<2.17.0",
                    column=29,
                    path=PATH,
                ),
            ),
            (
                "scrapy>=2.15.0,<=2.17.0",
                "from scrapy.utils.ssl import x509name_to_string",
                ExpectedIssue(
                    "SCP49 deprecated import: deprecated in scrapy 2.17.0; this "
                    "project supports scrapy >=2.15.0,<=2.17.0",
                    column=29,
                    path=PATH,
                ),
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
