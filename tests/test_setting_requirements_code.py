from __future__ import annotations

from packaging.version import Version

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
from .settings import default_issues

ZYTE_API_ADDON = "from scrapy_zyte_api import Addon\nADDONS = {Addon: 500}\n"

CASES: Cases = (
    # Checks based on requirements and code in a settings module
    *(
        (
            (
                File("[settings]\na=a", path="scrapy.cfg"),
                File("\n".join(requirements), path="requirements.txt"),
                File(code, path=path),
            ),
            (
                *default_issues(path),
                ExpectedIssue(
                    "SCP13 incomplete requirements freeze",
                    path="requirements.txt",
                ),
                *insecure_scrapy_issues(requirements),
                *iter_issues(issues),
            ),
            {},
        )
        for path in ("a.py",)
        for requirements, code, issues in (
            # Baseline
            (
                (),
                "",
                NO_ISSUE,
            ),
            # SCP36 invalid setting value: None allowed from a given version
            (
                ("scrapy==2.16.0",),
                "DOWNLOADER_CLIENT_TLS_CIPHERS = None",
                ExpectedIssue(
                    "SCP36 invalid setting value",
                    column=32,
                    path=path,
                ),
            ),
            (
                ("scrapy==2.17.0",),
                "DOWNLOADER_CLIENT_TLS_CIPHERS = None",
                NO_ISSUE,
            ),
            (
                (),
                "DOWNLOADER_CLIENT_TLS_CIPHERS = None",
                NO_ISSUE,
            ),
            # SCP34 missing changing setting
            (
                ("scrapy==2.13.0",),
                "",
                NO_ISSUE,
            ),
            (
                ("scrapy==2.13.0",),
                "TWISTED_REACTOR = 'twisted.internet.asyncioreactor.AsyncioSelectorReactor'",
                (
                    ExpectedIssue(
                        "SCP17 redundant setting value",
                        column=18,
                        path=path,
                    ),
                    ExpectedIssue(
                        "SCP41 unneeded import path",
                        column=18,
                        path=path,
                    ),
                ),
            ),
            (
                ("scrapy==2.12.0",),
                "",
                ExpectedIssue(
                    "SCP34 missing changing setting: TWISTED_REACTOR changes "
                    "from None to "
                    "'twisted.internet.asyncioreactor.AsyncioSelectorReactor' "
                    "in scrapy 2.13.0",
                    path=path,
                ),
            ),
            (
                ("scrapy==2.12.0",),
                "TWISTED_REACTOR = None",
                NO_ISSUE,
            ),
            (
                ("scrapy==2.12.0",),
                'TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"',
                ExpectedIssue(
                    "SCP41 unneeded import path",
                    column=18,
                    path=path,
                ),
            ),
            (
                ("scrapy==2.12.0",),
                'TWISTED_REACTOR = "custom.reactor"',
                ExpectedIssue(
                    "SCP41 unneeded import path",
                    column=18,
                    path=path,
                ),
            ),
            (
                ("scrapy==2.12.0",),
                'ADDONS = {"scrapy_zyte_api.Addon": 500}',
                (
                    ExpectedIssue(
                        "SCP41 unneeded import path",
                        column=10,
                        path=path,
                    ),
                    ExpectedIssue(
                        "SCP66 missing component requirement: scrapy-zyte-api",
                        column=10,
                        path=path,
                    ),
                ),
            ),
            (
                ("scrapy==2.12.0",),
                'ADDONS = {"scrapy_zyte_api.addon.Addon": 500}',
                (
                    ExpectedIssue(
                        "SCP41 unneeded import path",
                        column=10,
                        path=path,
                    ),
                    ExpectedIssue(
                        "SCP66 missing component requirement: scrapy-zyte-api",
                        column=10,
                        path=path,
                    ),
                ),
            ),
            (
                ("scrapy==2.12.0",),
                "ADDONS = {ScrapyZyteApiAddon: 500}",
                ExpectedIssue(
                    "SCP34 missing changing setting: TWISTED_REACTOR changes "
                    "from None to "
                    "'twisted.internet.asyncioreactor.AsyncioSelectorReactor' "
                    "in scrapy 2.13.0",
                    path=path,
                ),
            ),
            (
                ("scrapy==2.12.0",),
                "from scrapy_zyte_api import Addon\nADDONS = {Addon: 500}",
                NO_ISSUE,
            ),
            (
                ("scrapy==2.12.0",),
                (
                    "from scrapy_zyte_api import Addon as ScrapyZyteApiAddon\n"
                    ""
                    "ADDONS = {ScrapyZyteApiAddon: 500}"
                ),
                NO_ISSUE,
            ),
            (
                ("scrapy==2.12.0",),
                (
                    "from scrapy_zyte_api.addon import Addon as ScrapyZyteApiAddon\n"
                    ""
                    "ADDONS = {ScrapyZyteApiAddon: 500}"
                ),
                NO_ISSUE,
            ),
            (
                ("scrapy==2.12.0",),
                "import scrapy_zyte_api\nADDONS = {scrapy_zyte_api.Addon: 500}",
                NO_ISSUE,
            ),
            (
                ("scrapy==2.12.0",),
                (
                    "import scrapy_zyte_api.addon\n"
                    ""
                    "ADDONS = {scrapy_zyte_api.addon.Addon: 500}"
                ),
                NO_ISSUE,
            ),
            (
                ("scrapy==2.12.0",),
                "import scrapy_zyte_api.addon as foo\nADDONS = {foo.Addon: 500}",
                NO_ISSUE,
            ),
            (
                ("scrapy==2.12.0", "scrapy_zyte_api==0.30.0"),
                "import scrapy_zyte_api.addon as foo\nADDONS = {foo.Addon: 500}",
                NO_ISSUE,
            ),
            # SCP41 unneeded import path (non-based component priority dict)
            (
                ("scrapy==2.10.0",),
                "ADDONS = {ScrapyPoetAddon: 300}",
                (
                    ExpectedIssue(
                        (
                            "SCP34 missing changing setting: TWISTED_REACTOR "
                            "changes from None to "
                            "'twisted.internet.asyncioreactor.AsyncioSelectorReactor' "
                            "in scrapy 2.13.0"
                        ),
                        path=path,
                    ),
                ),
            ),
            (
                ("scrapy==2.10.0",),
                'ADDONS = {"scrapy_poet.addons.Addon": 300}',
                (
                    ExpectedIssue(
                        (
                            "SCP34 missing changing setting: TWISTED_REACTOR "
                            "changes from None to "
                            "'twisted.internet.asyncioreactor.AsyncioSelectorReactor' "
                            "in scrapy 2.13.0"
                        ),
                        path=path,
                    ),
                    ExpectedIssue(
                        "SCP41 unneeded import path",
                        column=10,
                        path=path,
                    ),
                    ExpectedIssue(
                        "SCP66 missing component requirement: scrapy-poet",
                        column=10,
                        path=path,
                    ),
                ),
            ),
            # SCP41 unneeded import path (base setting)
            (
                ("scrapy==2.4.0",),
                'EXTENSIONS_BASE = {"custom.Extension": 42}',
                (
                    ExpectedIssue("SCP33 base setting use", path=path),
                    ExpectedIssue(
                        (
                            "SCP34 missing changing setting: TWISTED_REACTOR "
                            "changes from None to "
                            "'twisted.internet.asyncioreactor.AsyncioSelectorReactor' "
                            "in scrapy 2.13.0"
                        ),
                        path=path,
                    ),
                ),
            ),
            # SCP17 redundant setting value: disabling a base key added later
            (
                ("scrapy==2.11.2",),
                'SPIDER_CONTRACTS = {"scrapy.contracts.default.MetadataContract": None}',
                (
                    ExpectedIssue(
                        (
                            "SCP34 missing changing setting: TWISTED_REACTOR "
                            "changes from None to "
                            "'twisted.internet.asyncioreactor.AsyncioSelectorReactor' "
                            "in scrapy 2.13.0"
                        ),
                        path=path,
                    ),
                    ExpectedIssue(
                        (
                            "SCP17 redundant setting value: "
                            "'scrapy.contracts.default.MetadataContract' is not "
                            "in SPIDER_CONTRACTS_BASE, so there is nothing to "
                            "disable"
                        ),
                        column=20,
                        path=path,
                    ),
                ),
            ),
            (
                ("scrapy==2.12.0",),
                'SPIDER_CONTRACTS = {"scrapy.contracts.default.MetadataContract": None}',
                (
                    ExpectedIssue(
                        (
                            "SCP34 missing changing setting: TWISTED_REACTOR "
                            "changes from None to "
                            "'twisted.internet.asyncioreactor.AsyncioSelectorReactor' "
                            "in scrapy 2.13.0"
                        ),
                        path=path,
                    ),
                ),
            ),
            # SCP41 unneeded import path: removed base key
            (
                ("scrapy==2.11.1",),
                'SPIDER_MIDDLEWARES = {"scrapy.spidermiddlewares.offsite.OffsiteMiddleware": 10}',
                (
                    ExpectedIssue(
                        (
                            "SCP34 missing changing setting: TWISTED_REACTOR "
                            "changes from None to "
                            "'twisted.internet.asyncioreactor.AsyncioSelectorReactor' "
                            "in scrapy 2.13.0"
                        ),
                        path=path,
                    ),
                ),
            ),
            (
                ("scrapy==2.11.2",),
                'SPIDER_MIDDLEWARES = {"scrapy.spidermiddlewares.offsite.OffsiteMiddleware": 10}',
                (
                    ExpectedIssue(
                        (
                            "SCP34 missing changing setting: TWISTED_REACTOR "
                            "changes from None to "
                            "'twisted.internet.asyncioreactor.AsyncioSelectorReactor' "
                            "in scrapy 2.13.0"
                        ),
                        path=path,
                    ),
                    ExpectedIssue("SCP41 unneeded import path", column=22, path=path),
                ),
            ),
            # SCP66 missing component requirement
            (
                (),
                'DOWNLOADER_MIDDLEWARES = {"scrapy_zyte_api.ScrapyZyteAPIDownloaderMiddleware": 633}',
                NO_ISSUE,
            ),
            (
                ("scrapy==2.13.0",),
                'DOWNLOADER_MIDDLEWARES = {"scrapy_zyte_api.ScrapyZyteAPIDownloaderMiddleware": 633}',
                (
                    ExpectedIssue("SCP41 unneeded import path", column=26, path=path),
                    ExpectedIssue(
                        "SCP66 missing component requirement: scrapy-zyte-api",
                        column=26,
                        path=path,
                    ),
                ),
            ),
            (
                ("scrapy==2.13.0", "scrapy-zyte-api==0.30.0"),
                'DOWNLOADER_MIDDLEWARES = {"scrapy_zyte_api.ScrapyZyteAPIDownloaderMiddleware": 633}',
                ExpectedIssue("SCP41 unneeded import path", column=26, path=path),
            ),
            (
                ("scrapy==2.13.0",),
                'DOWNLOADER_MIDDLEWARES = {"myproject.middlewares.MyMiddleware": 543}',
                ExpectedIssue("SCP41 unneeded import path", column=26, path=path),
            ),
            (
                ("scrapy==2.13.0",),
                'SCHEDULER = "scrapy_redis.scheduler.Scheduler"',
                (
                    ExpectedIssue("SCP41 unneeded import path", column=12, path=path),
                    ExpectedIssue(
                        "SCP66 missing component requirement: scrapy-redis",
                        column=12,
                        path=path,
                    ),
                ),
            ),
        )
    ),
    # SCP17 redundant setting value
    *(
        (
            [
                File("[settings]\na=a", path="scrapy.cfg"),
                File(f"scrapy=={version}", path="requirements.txt"),
                File(f"{name} = {value}", path=path),
            ],
            (
                *default_issues(path),
                ExpectedIssue(
                    "SCP13 incomplete requirements freeze",
                    path="requirements.txt",
                ),
                *(
                    (
                        ExpectedIssue(
                            "SCP14 unsupported requirement: scrapy-lint only supports scrapy 2.0.1+",
                            path="requirements.txt",
                        ),
                    )
                    if Version(version) < Version("2.0.1")
                    else ()
                ),
                *insecure_scrapy_issues(f"scrapy=={version}"),
                *(
                    (
                        ExpectedIssue(
                            "SCP17 redundant setting value",
                            column=len(name) + 3,
                            path=path,
                        ),
                    )
                    if should_trigger
                    else ()
                ),
            ),
            {},
        )
        for path in ["a.py"]
        for version, name, value, should_trigger in (
            # If a Scrapy version is known, SCP17 is still triggered or not as
            # usual for settings for which we do not know a history of default
            # value changes, but we do know their default value.
            (
                "2.13.0",
                "TELNETCONSOLE_USERNAME",
                '"scrapy"',
                True,
            ),
            (
                "2.13.0",
                "TELNETCONSOLE_USERNAME",
                '"username"',
                False,
            ),
        )
    ),
    *(
        (
            [
                File("[settings]\na=a", path="scrapy.cfg"),
                File(requirements, path="requirements.txt"),
                File('TELNETCONSOLE_USERNAME = "scrapy"', path=path),
            ],
            (
                *default_issues(path),
                *(
                    ExpectedIssue(
                        "SCP13 incomplete requirements freeze",
                        path="requirements.txt",
                    )
                    for _ in range(1)
                    if not isinstance(requirements, bytes)
                ),
                ExpectedIssue(
                    "SCP17 redundant setting value",
                    column=len("TELNETCONSOLE_USERNAME") + 3,
                    path=path,
                ),
            ),
            {},
        )
        for path in ["a.py"]
        for requirements in (
            # Invalid or non-frozen requirements do not prevent SCP17 for
            # settings for which SCP17 reporting does not depend on the version
            # of Scrapy.
            "",
            "# scrapy==2.13.0",
            "scrapy>=2.13.0",
            "scrapy>=2.13.0,<2.14.0",
            "scrapy!",
            "scrapy!=2.13.0  # foo",
            b"\xff\xfe\x00\x00",
        )
    ),
    # SCP17 redundant setting value: values that add-ons set
    *(
        (
            (
                File("[settings]\na=a", path="scrapy.cfg"),
                File(f"scrapy==2.19.0\n{requirements}\n", path="requirements.txt"),
                File(code, path=path),
            ),
            (
                *default_issues(path),
                ExpectedIssue(
                    "SCP13 incomplete requirements freeze",
                    path="requirements.txt",
                ),
                *iter_issues(issues),
            ),
            {},
        )
        for path in ("a.py",)
        for requirements, code, issues in (
            (
                "scrapy-zyte-api==0.36.0",
                f"{ZYTE_API_ADDON}ZYTE_API_TRANSPARENT_MODE = True",
                ExpectedIssue(
                    "SCP17 redundant setting value: already set by the "
                    "scrapy-zyte-api add-on",
                    line=3,
                    column=28,
                    path="a.py",
                ),
            ),
            # A different value is not redundant.
            (
                "scrapy-zyte-api==0.36.0",
                f"{ZYTE_API_ADDON}ZYTE_API_TRANSPARENT_MODE = False",
                NO_ISSUE,
            ),
            # Reverting what the add-on does is not redundant either, even
            # though the value matches the default value of Scrapy.
            (
                "scrapy-zyte-api==0.36.0",
                (
                    f"{ZYTE_API_ADDON}REQUEST_FINGERPRINTER_CLASS = "
                    '"scrapy.utils.request.RequestFingerprinter"'
                ),
                ExpectedIssue(
                    "SCP41 unneeded import path",
                    line=3,
                    column=30,
                    path="a.py",
                ),
            ),
            # ADDONS can be defined after the settings it affects.
            (
                "scrapy-zyte-api==0.36.0",
                (
                    "from scrapy_zyte_api import Addon\n"
                    "ZYTE_API_TRANSPARENT_MODE = True\n"
                    "ADDONS = {Addon: 500}"
                ),
                ExpectedIssue(
                    "SCP17 redundant setting value: already set by the "
                    "scrapy-zyte-api add-on",
                    line=2,
                    column=28,
                    path="a.py",
                ),
            ),
            # The add-on sets this one to whatever the project uses as
            # download handler, so its value is unknown (no SCP17).
            (
                "scrapy-zyte-api==0.36.0",
                (
                    f"{ZYTE_API_ADDON}ZYTE_API_FALLBACK_HTTP_HANDLER = "
                    '"scrapy.core.downloader.handlers.http.HTTPDownloadHandler"'
                ),
                ExpectedIssue(
                    "SCP41 unneeded import path",
                    line=3,
                    column=33,
                    path="a.py",
                ),
            ),
            # Add-ons are known one by one, so when 2 of them set the same
            # setting the resulting value is unknown, whichever of them the
            # settings module agrees with.
            *(
                (
                    "scrapy-poet==0.27.2\nscrapy-zyte-api==0.36.0",
                    (
                        "from scrapy_poet import Addon as PoetAddon\n"
                        "from scrapy_zyte_api import Addon\n"
                        "ADDONS = {PoetAddon: 300, Addon: 500}\n"
                        f'REQUEST_FINGERPRINTER_CLASS = "{fingerprinter}"'
                    ),
                    ExpectedIssue(
                        "SCP41 unneeded import path",
                        line=4,
                        column=30,
                        path="a.py",
                    ),
                )
                for fingerprinter in (
                    "scrapy_poet.ScrapyPoetRequestFingerprinter",
                    "scrapy_zyte_api.ScrapyZyteAPIRequestFingerprinter",
                )
            ),
            # A version older than any known one gets the oldest known data.
            (
                "scrapy-zyte-api==0.17.0",
                (
                    f"{ZYTE_API_ADDON}DOWNLOADER_MIDDLEWARES = "
                    '{"scrapy_zyte_api.ScrapyZyteAPIDownloaderMiddleware": 1000}'
                ),
                (
                    ExpectedIssue(
                        "SCP76 incompatible requirement: scrapy 2.14.0+ "
                        "requires scrapy-zyte-api 0.32.0+",
                        line=2,
                        path="requirements.txt",
                    ),
                    ExpectedIssue(
                        "SCP76 incompatible requirement: scrapy 2.18.0+ "
                        "requires scrapy-zyte-api 0.36.0+",
                        line=2,
                        path="requirements.txt",
                    ),
                    ExpectedIssue(
                        "SCP17 redundant setting value: already set by the "
                        "scrapy-zyte-api add-on",
                        line=3,
                        column=25,
                        path="a.py",
                    ),
                    ExpectedIssue(
                        "SCP41 unneeded import path",
                        line=3,
                        column=26,
                        path="a.py",
                    ),
                ),
            ),
        )
    ),
    # SCP27 unknown setting: recommend known-settings even when
    # dependency versions need to be taken into account (assume they are met)
    (
        (
            File("", path="scrapy.cfg"),
            File("scrapy", path="requirements.txt"),
            File("settings['SETING']", path="a.py"),
        ),
        (
            ExpectedIssue(
                message="SCP13 incomplete requirements freeze",
                line=1,
                column=0,
                path="requirements.txt",
            ),
            ExpectedIssue(
                "SCP27 unknown setting: did you mean: SETTING?",
                column=9,
                path="a.py",
            ),
        ),
        {
            "known-settings": ["SETTING"],
        },
    ),
)


@cases(CASES)
def test(
    files: File | list[File],
    expected: ExpectedIssue | list[ExpectedIssue] | None,
    options,
):
    check_project(files, expected, options)
