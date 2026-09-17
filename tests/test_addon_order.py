from __future__ import annotations

from tests.helpers import check_project
from tests.settings import default_issues

from . import Cases, ExpectedIssue, File, cases, iter_issues

PATH = "a.py"
DUD = "duplicate_url_discarder.Addon"
POET = "scrapy_poet.Addon"
ZYTE_API = "scrapy_zyte_api.Addon"
ZYTE_API_LONG = "scrapy_zyte_api.addon.Addon"


def issue(code: str, addon: str, after: str) -> ExpectedIssue:
    """SCP80 for *addon*, expected at its priority value within *code*."""
    for line, text in enumerate(code.splitlines(), start=1):
        index = text.find(addon)
        if index == -1:
            continue
        return ExpectedIssue(
            f"SCP80 wrong add-on order: {addon} must run after {after}",
            line=line,
            column=text.index(": ", index + len(addon)) + 2,
            path=PATH,
        )
    raise AssertionError(addon)


CASES: Cases = tuple(
    (
        [
            File("[settings]\na=a", path="scrapy.cfg"),
            File(code, path=PATH),
        ],
        (
            *default_issues(PATH),
            *(issue(code, addon, after) for addon, after in wrong_order),
            *iter_issues(other_issues),
        ),
        {},
    )
    for code, wrong_order, other_issues in (
        # Add-ons that wrap the request fingerprinter of the add-ons before
        # them need a higher priority value, which is what runs them later.
        (
            f'ADDONS = {{"{ZYTE_API}": 100, "{DUD}": 200}}',
            (),
            None,
        ),
        (
            f'ADDONS = {{"{DUD}": 200, "{ZYTE_API}": 100}}',
            (),
            None,
        ),
        (
            f'ADDONS = {{"{ZYTE_API}": 200, "{DUD}": 100}}',
            ((DUD, ZYTE_API),),
            None,
        ),
        # Scrapy sorts add-ons with a stable sort, so add-ons sharing a
        # priority value run in definition order.
        (
            f'ADDONS = {{"{ZYTE_API}": 100, "{DUD}": 100}}',
            (),
            None,
        ),
        (
            f'ADDONS = {{"{DUD}": 100, "{ZYTE_API}": 100}}',
            ((DUD, ZYTE_API),),
            None,
        ),
        # The whole fingerprinter chain is checked.
        (
            f'ADDONS = {{"{POET}": 100, "{ZYTE_API}": 200, "{DUD}": 300}}',
            (),
            None,
        ),
        (
            f'ADDONS = {{"{DUD}": 100, "{ZYTE_API}": 200, "{POET}": 300}}',
            ((DUD, POET), (DUD, ZYTE_API), (ZYTE_API, POET)),
            None,
        ),
        # Add-ons with no order requirement between them are unaffected.
        (
            f'ADDONS = {{"{DUD}": 100, "zyte_spider_templates.Addon": 200}}',
            (),
            None,
        ),
        (
            f'ADDONS = {{"{DUD}": 100, "unknown.Addon": 50}}',
            (),
            None,
        ),
        # A None value disables the add-on, and a value that is not a literal
        # number cannot be compared.
        (
            f'ADDONS = {{"{DUD}": None, "{ZYTE_API}": 100}}',
            (),
            ExpectedIssue(
                "SCP36 invalid setting value: dict values must be integers, "
                "not NoneType (None)",
                column=43,
                path=PATH,
            ),
        ),
        (
            f'ADDONS = {{"{DUD}": PRIORITY, "{ZYTE_API}": 100}}',
            (),
            None,
        ),
        # Add-ons are matched by package, whichever import path or object is
        # used for them.
        (
            (
                "import duplicate_url_discarder\n"
                "import scrapy_zyte_api.addon\n"
                "ADDONS = {\n"
                "    duplicate_url_discarder.Addon: 100,\n"
                "    scrapy_zyte_api.addon.Addon: 200,\n"
                "}"
            ),
            ((DUD, ZYTE_API_LONG),),
            None,
        ),
    )
)


@cases(CASES)
def test(files, expected, options):
    check_project(files, expected, options)
