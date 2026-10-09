from __future__ import annotations

from packaging.version import Version

from tests.helpers import check_project
from tests.settings import default_issues

from . import Cases, ExpectedIssue, File, cases, insecure_scrapy_issues, iter_issues

PATH = "a.py"
OLD = "scrapy==2.14.2"
NEW = "scrapy==2.15.0"
RETRY = "scrapy.downloadermiddlewares.retry.RetryMiddleware"
OFFSITE = "scrapy.downloadermiddlewares.offsite.OffsiteMiddleware"


def invalid(path: str, line: int, column: int) -> ExpectedIssue:
    return ExpectedIssue(
        f"SCP81 invalid component deactivation: before Scrapy 2.15.0, only "
        f"{path!r} disables the base setting entry",
        line=line,
        column=column,
        path=PATH,
    )


def noop(setting: str, path: str, line: int, column: int) -> ExpectedIssue:
    return ExpectedIssue(
        f"SCP17 redundant setting value: {path!r} is not in {setting}_BASE, so "
        f"there is nothing to disable",
        line=line,
        column=column,
        path=PATH,
    )


CASES: Cases = tuple(
    (
        [
            File("[settings]\na=a", path="scrapy.cfg"),
            *((File(requirements, path="requirements.txt"),) if requirements else ()),
            File(code, path=PATH),
        ],
        (
            *default_issues(PATH),
            *(
                (
                    ExpectedIssue(
                        "SCP13 incomplete requirements freeze",
                        path="requirements.txt",
                    ),
                    *(
                        (
                            ExpectedIssue(
                                (
                                    "SCP34 missing changing setting: "
                                    "TWISTED_REACTOR changes from None to "
                                    "'twisted.internet.asyncioreactor."
                                    "AsyncioSelectorReactor' in scrapy 2.13.0"
                                ),
                                path=PATH,
                            ),
                        )
                        if Version(requirements.partition("==")[2]) < Version("2.13")
                        else ()
                    ),
                    *insecure_scrapy_issues(requirements),
                )
                if requirements
                else ()
            ),
            *iter_issues(issues),
        ),
        {},
    )
    for requirements, code, issues in (
        # The import path string of a base setting entry disables it.
        (None, f'DOWNLOADER_MIDDLEWARES = {{"{RETRY}": None}}', None),
        # Before Scrapy 2.15.0, an object key does not, whichever way it is
        # imported.
        (
            OLD,
            (
                "from scrapy.downloadermiddlewares.retry import RetryMiddleware\n"
                "DOWNLOADER_MIDDLEWARES = {RetryMiddleware: None}"
            ),
            invalid(RETRY, 2, 26),
        ),
        (
            OLD,
            (
                "from scrapy.downloadermiddlewares import retry\n"
                "DOWNLOADER_MIDDLEWARES = {retry.RetryMiddleware: None}"
            ),
            invalid(RETRY, 2, 26),
        ),
        (
            OLD,
            (
                "import scrapy.downloadermiddlewares.retry\n"
                "DOWNLOADER_MIDDLEWARES = {\n"
                f"    {RETRY}: None,\n"
                "}"
            ),
            invalid(RETRY, 3, 4),
        ),
        # Since Scrapy 2.15.0 keys match by the object they import, and
        # without a frozen Scrapy version that may be the case.
        *(
            (
                requirements,
                (
                    "from scrapy.downloadermiddlewares.retry import "
                    "RetryMiddleware\n"
                    "DOWNLOADER_MIDDLEWARES = {RetryMiddleware: None}"
                ),
                None,
            )
            for requirements in (NEW, None)
        ),
        # Only None values are checked.
        (
            OLD,
            (
                "from scrapy.downloadermiddlewares.retry import RetryMiddleware\n"
                "DOWNLOADER_MIDDLEWARES = {RetryMiddleware: 100}"
            ),
            None,
        ),
        # Keys that are not import paths, as strings or as objects, are
        # reported as invalid values instead.
        (
            None,
            "DOWNLOADER_MIDDLEWARES = {1: None}",
            ExpectedIssue(
                "SCP36 invalid setting value: keys must be strings, not int (1)",
                column=26,
                path=PATH,
            ),
        ),
        # An import path string is the only way to disable a component before
        # Scrapy 2.15.0, so it is not reported as unneeded until then.
        (
            OLD,
            'DOWNLOADER_MIDDLEWARES = {"custom.Middleware": None}',
            noop("DOWNLOADER_MIDDLEWARES", "custom.Middleware", 1, 26),
        ),
        (
            NEW,
            'DOWNLOADER_MIDDLEWARES = {"custom.Middleware": None}',
            (
                ExpectedIssue("SCP41 unneeded import path", column=26, path=PATH),
                noop("DOWNLOADER_MIDDLEWARES", "custom.Middleware", 1, 26),
            ),
        ),
        # A key that is in no base setting disables nothing.
        (
            None,
            'DOWNLOADER_MIDDLEWARES = {"custom.Middleware": None}',
            noop("DOWNLOADER_MIDDLEWARES", "custom.Middleware", 1, 26),
        ),
        (
            None,
            (
                "from custom import Middleware\n"
                "DOWNLOADER_MIDDLEWARES = {Middleware: None}"
            ),
            noop("DOWNLOADER_MIDDLEWARES", "custom.Middleware", 2, 26),
        ),
        (
            None,
            'DOWNLOAD_HANDLERS = {"ftp": None, "gopher": None}',
            noop("DOWNLOAD_HANDLERS", "gopher", 1, 34),
        ),
        # Unless an add-on may enable it: one that scrapy-lint does not know,
        # or a known one that changes the setting, wherever it is defined.
        (
            None,
            (
                'ADDONS = {"custom.Addon": 100}\n'
                'DOWNLOADER_MIDDLEWARES = {"custom.Middleware": None}'
            ),
            None,
        ),
        (
            None,
            (
                'DOWNLOADER_MIDDLEWARES = {"scrapy_poet.InjectionMiddleware": None}\n'
                'ADDONS = {"scrapy_poet.Addon": 100}'
            ),
            None,
        ),
        (
            None,
            (
                'ADDONS = {"scrapy_poet.Addon": 100}\n'
                'EXTENSIONS = {"custom.Extension": None}'
            ),
            noop("EXTENSIONS", "custom.Extension", 2, 14),
        ),
        # The base setting of the frozen Scrapy version is used when known,
        # and the union of all known versions otherwise.
        (None, f'DOWNLOADER_MIDDLEWARES = {{"{OFFSITE}": None}}', None),
        ("scrapy==2.11.2", f'DOWNLOADER_MIDDLEWARES = {{"{OFFSITE}": None}}', None),
        (
            "scrapy==2.11.1",
            f'DOWNLOADER_MIDDLEWARES = {{"{OFFSITE}": None}}',
            noop("DOWNLOADER_MIDDLEWARES", OFFSITE, 1, 26),
        ),
    )
)


@cases(CASES)
def test(files, expected, options):
    check_project(files, expected, options)
