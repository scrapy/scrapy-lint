from . import NO_ISSUE, Cases, ExpectedIssue, File, cases
from .helpers import check_project

EOL_STACK = "scrapy:2.4-20210927"  # Python 3.8
SUPPORTED_STACK = "scrapy:2.13-20250721"  # Python 3.12
EOL_PYTHON = "3.9.23"
SUPPORTED_PYTHON = "3.12.11"
NO_ROOT_REQUIREMENTS = ExpectedIssue(
    message="SCP21 no root requirements",
    path="scrapinghub.yml",
)
SCRAPY_CFG = File("", path="scrapy.cfg")


def python_version(text: str) -> File:
    return File(text, path=".python-version")


def pyproject(text: str) -> File:
    return File(text, path="pyproject.toml")


def stack(value: str) -> File:
    return File(f"stack: {value}\n", path="scrapinghub.yml")


def stack_issue(message: str) -> ExpectedIssue:
    return ExpectedIssue(message=message, line=1, column=7, path="scrapinghub.yml")


def eol_issue(key: str, series: str, eol: str) -> str:
    return (
        f"SCP47 end-of-life Python: {key} allows Python {series}, which "
        f"reached its end of life on {eol}"
    )


def unfrozen_issue(key: str, value: str) -> str:
    return (
        f"SCP49 Python not frozen: {key} ({value}) allows more than one Python version"
    )


CASES: Cases = (
    # .python-version
    *(
        ((SCRAPY_CFG, python_version(text)), issues, {})
        for text, issues in (
            (f"{SUPPORTED_PYTHON}\n", NO_ISSUE),
            (
                f"{EOL_PYTHON}\n",
                ExpectedIssue(
                    message=eol_issue(".python-version", "3.9", "2025-10-31"),
                    path=".python-version",
                ),
            ),
            ("3.12\n", NO_ISSUE),
            # Comments and empty lines come before the version.
            (f"# Set by uv\n\n{SUPPORTED_PYTHON}\n", NO_ISSUE),
            # Files with no version and files with an invalid version declare
            # nothing.
            ("# Set by uv\n", NO_ISSUE),
            ("system\n", NO_ISSUE),
        )
    ),
    # requires-python
    *(
        ((SCRAPY_CFG, pyproject(f"[project]\n{text}\n")), issues, {})
        for text, issues in (
            (f'requires-python = "=={SUPPORTED_PYTHON}"', NO_ISSUE),
            ('requires-python = "==3.12.*"', NO_ISSUE),
            ('requires-python = "~=3.12.0"', NO_ISSUE),
            (
                'requires-python = "~=3.12"',
                ExpectedIssue(
                    message=unfrozen_issue("requires-python", "~=3.12"),
                    line=2,
                    path="pyproject.toml",
                ),
            ),
            (
                'requires-python = ">=3.12"',
                ExpectedIssue(
                    message=unfrozen_issue("requires-python", ">=3.12"),
                    line=2,
                    path="pyproject.toml",
                ),
            ),
            (
                'requires-python = ">=3.9,<4.0"',
                (
                    ExpectedIssue(
                        message=unfrozen_issue("requires-python", ">=3.9,<4.0"),
                        line=2,
                        path="pyproject.toml",
                    ),
                    ExpectedIssue(
                        message=eol_issue("requires-python", "3.9", "2025-10-31"),
                        line=2,
                        path="pyproject.toml",
                    ),
                ),
            ),
            # Ranges of unknown Python versions.
            (
                'requires-python = ">=3.99"',
                ExpectedIssue(
                    message=unfrozen_issue("requires-python", ">=3.99"),
                    line=2,
                    path="pyproject.toml",
                ),
            ),
            # Invalid or absent declarations.
            ('requires-python = "3 or newer"', NO_ISSUE),
            ("requires-python = 312", NO_ISSUE),
            ('name = "toscrape-com"', NO_ISSUE),
        )
    ),
    # .python-version comes before requires-python.
    (
        (
            SCRAPY_CFG,
            python_version(f"{SUPPORTED_PYTHON}\n"),
            pyproject('[project]\nrequires-python = ">=3.9"\n'),
        ),
        NO_ISSUE,
        {},
    ),
    # Stack Python
    *(
        ((SCRAPY_CFG, stack(value)), (NO_ROOT_REQUIREMENTS, *issues), {})
        for value, issues in (
            (
                EOL_STACK,
                (
                    stack_issue(
                        "SCP47 end-of-life Python: stack Python 3.8 reached its "
                        "end of life on 2024-10-07",
                    ),
                ),
            ),
            (SUPPORTED_STACK, ()),
            # Stacks with no known Python version.
            ("scrapy:9.9-20250721", ()),
            ("custom:1.0-20250721", ()),
        )
    ),
    # Stack Python against the declared Python
    *(
        (
            (SCRAPY_CFG, stack(SUPPORTED_STACK), python_version(f"{version}\n")),
            (NO_ROOT_REQUIREMENTS, *issues),
            {},
        )
        for version, issues in (
            (SUPPORTED_PYTHON, ()),
            (
                "3.13.5",
                (
                    stack_issue(
                        "SCP48 stack Python mismatch: stack Python 3.12 does "
                        "not match .python-version (3.13.5)",
                    ),
                ),
            ),
        )
    ),
    (
        (
            SCRAPY_CFG,
            stack(SUPPORTED_STACK),
            pyproject('[project]\nrequires-python = ">=3.13"\n'),
        ),
        (
            NO_ROOT_REQUIREMENTS,
            ExpectedIssue(
                message=unfrozen_issue("requires-python", ">=3.13"),
                line=2,
                path="pyproject.toml",
            ),
            stack_issue(
                "SCP48 stack Python mismatch: stack Python 3.12 does not match "
                "requires-python (>=3.13)",
            ),
        ),
        {},
    ),
    # Declarations that allow no known Python version say nothing about the
    # stack.
    (
        (
            SCRAPY_CFG,
            stack(SUPPORTED_STACK),
            pyproject('[project]\nrequires-python = ">=3.99"\n'),
        ),
        (
            NO_ROOT_REQUIREMENTS,
            ExpectedIssue(
                message=unfrozen_issue("requires-python", ">=3.99"),
                line=2,
                path="pyproject.toml",
            ),
        ),
        {},
    ),
)


@cases(CASES)
def test(files, expected, options):
    check_project(files, expected, options)
