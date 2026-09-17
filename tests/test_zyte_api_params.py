from __future__ import annotations

from tests.helpers import check_project
from tests.settings import default_issues

from . import NO_ISSUE, Cases, ExpectedIssue, File, cases, iter_issues

SETTINGS_PATH = "proj/settings.py"
SPIDER_PATH = "proj/spiders/a.py"
POET_REQUIREMENTS = "scrapy-poet==0.26.0\nscrapy-zyte-api==0.44.0"
FREEZE_ISSUE = ExpectedIssue(
    "SCP13 incomplete requirements freeze",
    path="requirements.txt",
)


def issue(detail: str, path: str = SETTINGS_PATH, **kwargs) -> ExpectedIssue:
    return ExpectedIssue(
        f"SCP78 inconsistent Zyte API params: {detail}",
        path=path,
        **kwargs,
    )


def files(
    settings: str,
    requirements: str = POET_REQUIREMENTS,
    spider: str | None = None,
) -> list[File]:
    result = [
        File("[settings]\ndefault = proj.settings", path="scrapy.cfg"),
        File(requirements, path="requirements.txt"),
        File(settings, path=SETTINGS_PATH),
    ]
    if spider is not None:
        result.append(File(spider, path=SPIDER_PATH))
    return result


def spider_code(custom_settings: str) -> str:
    return f"class A:\n    custom_settings = {custom_settings}"


AUTOMAP = '\nZYTE_API_AUTOMAP_PARAMS = {"geolocation": "US"}'
PROVIDER = '\nZYTE_API_PROVIDER_PARAMS = {"geolocation": "US"}'

MODULE_GAP_ISSUE = issue(
    "geolocation is missing from ZYTE_API_PROVIDER_PARAMS",
    line=2,
    column=27,
)

SETTING_CASES: Cases = tuple(
    (files(settings, requirements), (*iter_issues(issues),), {})
    for settings, requirements, issues in (
        # Matching params are what the rule asks for.
        (f"{AUTOMAP}{PROVIDER}", POET_REQUIREMENTS, NO_ISSUE),
        # Params meant for a single request mode are not global params.
        (
            (
                '\nZYTE_API_AUTOMAP_PARAMS = {"httpResponseBody": True}'
                '\nZYTE_API_PROVIDER_PARAMS = {"productOptions": {}}'
            ),
            POET_REQUIREMENTS,
            NO_ISSUE,
        ),
        # A global param in one setting only does not reach the other mode.
        (
            AUTOMAP,
            POET_REQUIREMENTS,
            MODULE_GAP_ISSUE,
        ),
        (
            PROVIDER,
            POET_REQUIREMENTS,
            issue(
                "geolocation is missing from ZYTE_API_AUTOMAP_PARAMS",
                line=2,
                column=28,
            ),
        ),
        (
            '\nZYTE_API_PROVIDER_PARAMS = {"ipType": "residential"}',
            POET_REQUIREMENTS,
            issue(
                "ipType is missing from ZYTE_API_AUTOMAP_PARAMS",
                line=2,
                column=28,
            ),
        ),
        # Different values are as silent a mismatch as a missing param.
        (
            f'{AUTOMAP}\nZYTE_API_PROVIDER_PARAMS = {{"geolocation": "IE"}}',
            POET_REQUIREMENTS,
            issue(
                "geolocation is 'US' in ZYTE_API_AUTOMAP_PARAMS and 'IE' in "
                "ZYTE_API_PROVIDER_PARAMS",
                line=2,
                column=27,
            ),
        ),
        # Values that cannot be resolved are not compared.
        (
            f"{AUTOMAP}\nZYTE_API_PROVIDER_PARAMS = {{'geolocation': COUNTRY}}",
            POET_REQUIREMENTS,
            NO_ISSUE,
        ),
        (
            f"{PROVIDER}\nZYTE_API_AUTOMAP_PARAMS = PARAMS",
            POET_REQUIREMENTS,
            NO_ISSUE,
        ),
        # Without the provider, automap params are the only params in play.
        (AUTOMAP, "scrapy-zyte-api==0.44.0", NO_ISSUE),
        # The provider also comes from an extra or an indirect requirement.
        (
            AUTOMAP,
            "scrapy-zyte-api[provider]==0.44.0",
            MODULE_GAP_ISSUE,
        ),
        (
            AUTOMAP,
            "zyte-spider-templates==0.14.0\nscrapy-zyte-api==0.44.0",
            MODULE_GAP_ISSUE,
        ),
    )
)

CUSTOM_SETTINGS_CASES: Cases = tuple(
    (files(settings, spider=spider), (*iter_issues(issues),), {})
    for settings, spider, issues in (
        # Project settings fill the gaps that custom_settings leave.
        (
            f"{AUTOMAP}{PROVIDER}",
            spider_code('{"ZYTE_API_AUTOMAP_PARAMS": {}}'),
            issue(
                "geolocation is missing from ZYTE_API_AUTOMAP_PARAMS",
                path=SPIDER_PATH,
                line=2,
                column=23,
            ),
        ),
        (
            AUTOMAP,
            spider_code('{"ZYTE_API_PROVIDER_PARAMS": {"geolocation": "US"}}'),
            MODULE_GAP_ISSUE,
        ),
        (
            AUTOMAP,
            spider_code('{"ZYTE_API_PROVIDER_PARAMS": {"geolocation": "IE"}}'),
            (
                MODULE_GAP_ISSUE,
                issue(
                    "geolocation is 'US' in ZYTE_API_AUTOMAP_PARAMS and 'IE' in "
                    "ZYTE_API_PROVIDER_PARAMS",
                    path=SPIDER_PATH,
                    line=2,
                    column=52,
                ),
            ),
        ),
        # A spider that overrides neither setting is covered by the settings
        # module alone.
        (
            f"{AUTOMAP}{PROVIDER}",
            spider_code('{"DOWNLOAD_DELAY": 1}'),
            NO_ISSUE,
        ),
        (
            f"{AUTOMAP}{PROVIDER}",
            spider_code("EXTRA_SETTINGS"),
            NO_ISSUE,
        ),
    )
)

CASES: Cases = tuple(
    (
        case_files,
        [FREEZE_ISSUE, *default_issues(SETTINGS_PATH), *iter_issues(expected)],
        options,
    )
    for case_files, expected, options in (*SETTING_CASES, *CUSTOM_SETTINGS_CASES)
)


@cases(CASES)
def test(files, expected, options):  # pylint: disable=redefined-outer-name
    check_project(files, expected, options)


def test_unparseable_setting_module():
    """A settings module that cannot be parsed contributes no params."""
    check_project(
        files(
            "(",
            spider=spider_code(
                '{"ZYTE_API_AUTOMAP_PARAMS": {"geolocation": "US"}}',
            ),
        ),
        issue(
            "geolocation is missing from ZYTE_API_PROVIDER_PARAMS",
            path=SPIDER_PATH,
            line=2,
            column=51,
        ),
        args=[SPIDER_PATH],
    )
