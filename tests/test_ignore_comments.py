from __future__ import annotations

from inspect import cleandoc

from . import NO_ISSUE, Cases, ExpectedIssue, File, cases
from .helpers import check_project, fix_project

URL_IN_ALLOWED_DOMAINS = 'allowed_domains = ["https://a.example"]'


def issue(line: int = 1) -> ExpectedIssue:
    return ExpectedIssue(
        message="SCP02 URL in allowed_domains",
        line=line,
        column=19,
        path="a.py",
    )


CASES: Cases = (
    (
        File(f"{URL_IN_ALLOWED_DOMAINS}  # scrapy-lint: ignore", path="a.py"),
        NO_ISSUE,
        {},
    ),
    (
        File(f"{URL_IN_ALLOWED_DOMAINS}  # scrapy-lint: ignore[SCP02]", path="a.py"),
        NO_ISSUE,
        {},
    ),
    (
        File(
            f"{URL_IN_ALLOWED_DOMAINS}  # scrapy-lint: ignore[SCP01, SCP02]",
            path="a.py",
        ),
        NO_ISSUE,
        {},
    ),
    (
        File(f"{URL_IN_ALLOWED_DOMAINS}  # SCRAPY-LINT: IGNORE[scp02]", path="a.py"),
        NO_ISSUE,
        {},
    ),
    # Codes other than the listed ones are still reported.
    (
        File(f"{URL_IN_ALLOWED_DOMAINS}  # scrapy-lint: ignore[SCP01]", path="a.py"),
        issue(),
        {},
    ),
    # An empty code list ignores nothing.
    (
        File(f"{URL_IN_ALLOWED_DOMAINS}  # scrapy-lint: ignore[]", path="a.py"),
        issue(),
        {},
    ),
    (
        File(f"{URL_IN_ALLOWED_DOMAINS}  # noqa: SCP02", path="a.py"),
        issue(),
        {},
    ),
    # A comment only affects the line where it is.
    (
        File(
            f"{URL_IN_ALLOWED_DOMAINS}  # scrapy-lint: ignore\n"
            f"{URL_IN_ALLOWED_DOMAINS}\n",
            path="a.py",
        ),
        issue(line=2),
        {},
    ),
    # Comments also work on non-Python files.
    (
        (
            File("scrapy==2.11.1  # scrapy-lint: ignore", path="requirements.txt"),
            File(
                cleandoc(
                    """
                    requirements:
                      file: requirements.txt
                    stack: scrapy:2.12  # scrapy-lint: ignore[SCP20]
                    """,
                ),
                path="scrapinghub.yml",
            ),
        ),
        NO_ISSUE,
        {},
    ),
)


@cases(CASES)
def test(
    files: File | list[File],
    expected: ExpectedIssue | list[ExpectedIssue] | None,
    options,
):
    check_project(files, expected, options)


def test_fix():
    """Issues ignored by a comment are not fixed."""
    fix_project(
        File(
            'allowed_domains = ["https://a.example"]\n'
            'allowed_domains = ["https://b.example"]  # scrapy-lint: ignore[SCP02]\n',
            path="a.py",
        ),
        File(
            'allowed_domains = ["a.example"]\n'
            'allowed_domains = ["https://b.example"]  # scrapy-lint: ignore[SCP02]\n',
            path="a.py",
        ),
        expected_fixed=1,
    )
