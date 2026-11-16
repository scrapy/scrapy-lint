from __future__ import annotations

from inspect import cleandoc
from pathlib import Path

import pytest

from scrapy_lint import main
from scrapy_lint._ignore_comments import preceding_ignore_comments

from . import NO_ISSUE, Cases, ExpectedIssue, File, cases, project
from .helpers import check_project, fix_project

URL_IN_ALLOWED_DOMAINS = 'allowed_domains = ["https://a.example"]'
STACK_IMAGE = "scrapinghub/scrapinghub-stack-scrapy"
DOCKER_PROJECT = (
    File("", path="scrapy.cfg"),
    File("image: true\n", path="scrapinghub.yml"),
)


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
                    stack: scrapy:2.12  # scrapy-lint: ignore[SCP20, SCP72]
                    """,
                ),
                path="scrapinghub.yml",
            ),
        ),
        NO_ISSUE,
        {},
    ),
    # Comments inside strings do not count.
    (
        File(f'{URL_IN_ALLOWED_DOMAINS}; "# scrapy-lint: ignore"', path="a.py"),
        issue(),
        {},
    ),
    # Lines that cannot take a comment are covered by the comment at the end of
    # the next line that can.
    (
        File(
            'allowed_domains = ["https://a.example", """\n'
            '"""]  # scrapy-lint: ignore[SCP02]\n'
            'x = settings["FOO"] + \\\n'
            "    1  # scrapy-lint: ignore[SCP27]\n",
            path="a.py",
        ),
        NO_ISSUE,
        {},
    ),
    # In Dockerfiles and .python-version files, comments cover the next
    # instruction.
    (
        (
            *DOCKER_PROJECT,
            File(
                cleandoc(
                    f"""
                    # syntax=docker/dockerfile:1
                    # scrapy-lint: ignore[SCP20]
                    FROM {STACK_IMAGE}:2.12
                    """,
                ),
                path="Dockerfile",
            ),
            File("# scrapy-lint: ignore[SCP63]\n3.9.23\n", path=".python-version"),
        ),
        NO_ISSUE,
        {},
    ),
    (
        (
            *DOCKER_PROJECT,
            File(
                f"# scrapy-lint: ignore[SCP20]\nRUN true\nFROM {STACK_IMAGE}:2.12\n",
                path="Dockerfile",
            ),
        ),
        ExpectedIssue(
            message="SCP20 stack not frozen",
            line=3,
            column=5,
            path="Dockerfile",
        ),
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


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (
            f"{URL_IN_ALLOWED_DOMAINS}\n",
            f"{URL_IN_ALLOWED_DOMAINS}  # scrapy-lint: ignore[SCP02]\n",
        ),
        # Issues on the same line share a comment, which keeps codes already
        # listed.
        (
            (
                'x = [settings["FOO"], settings["BAR"]]  # noqa\n'
                'y = settings["FOO"]  # scrapy-lint: ignore[SCP01]\n'
            ),
            (
                'x = [settings["FOO"], settings["BAR"]]  # noqa  # scrapy-lint: '
                "ignore[SCP27]\n"
                'y = settings["FOO"]  # scrapy-lint: ignore[SCP01, SCP27]\n'
            ),
        ),
        (
            'allowed_domains = ["https://a.example", """\n"""]',
            (
                'allowed_domains = ["https://a.example", """\n"""]  # scrapy-lint: '
                "ignore[SCP02]"
            ),
        ),
    ],
)
def test_add_ignore_python(capsys, source, expected):
    with project(File(source, path="a.py")):
        main(["--add-ignore"])
        assert Path("a.py").read_text(encoding="utf-8") == expected
        main([])
    out, _ = capsys.readouterr()
    assert out.startswith("Ignored ")


def test_add_ignore_preceding(capsys):
    files = [
        *DOCKER_PROJECT,
        File(
            f"# scrapy-lint: ignore[SCP01]\nFROM {STACK_IMAGE}:2.12\n"
            f"  FROM {STACK_IMAGE}:2.12\n",
            path="Dockerfile",
        ),
        File("# Set by uv\n3.9.23\n", path=".python-version"),
    ]
    with project(files):
        main(["--add-ignore"])
        assert Path("Dockerfile").read_text(encoding="utf-8") == (
            f"# scrapy-lint: ignore[SCP01, SCP20]\nFROM {STACK_IMAGE}:2.12\n"
            f"  # scrapy-lint: ignore[SCP20]\n  FROM {STACK_IMAGE}:2.12\n"
        )
        assert Path(".python-version").read_text(encoding="utf-8") == (
            "# Set by uv\n# scrapy-lint: ignore[SCP63]\n3.9.23\n"
        )
        main([])
    out, _ = capsys.readouterr()
    assert out == "Ignored 3 error(s).\n"


def test_dockerfile_instructions():
    """A comment covers every line of the next Dockerfile instruction."""
    ignore_comments = preceding_ignore_comments(
        cleandoc(
            """
            # escape=`
            # scrapy-lint: ignore
            RUN true `
                # comment
                && true
            RUN true \\
            FROM a
            """,
        ),
        dockerfile=True,
    )
    assert ignore_comments.anchors == {3: 3, 4: 3, 5: 3, 6: 6, 7: 7}
    assert set(ignore_comments.comments) == {3}


FILE_LEVEL_PROJECT = (
    File("", path="scrapy.cfg"),
    File("requirements:\n  file: requirements.txt\n", path="scrapinghub.yml"),
    File("", path="requirements.txt"),
)


@pytest.mark.parametrize(
    ("pyproject", "expected"),
    [
        (
            None,
            cleandoc(
                """
                [tool.scrapy-lint.per-file-ignores]
                "/requirements.txt" = ["SCP13"]
                "/scrapinghub.yml" = ["SCP18"]
                """,
            )
            + "\n",
        ),
        # Existing options are kept, and codes are added to existing entries.
        (
            cleandoc(
                """
                [project]
                name = "a"

                [tool.scrapy-lint.per-file-ignores]
                "/scrapinghub.yml" = ["SCP01"]  # why
                """,
            )
            + "\n",
            cleandoc(
                """
                [project]
                name = "a"

                [tool.scrapy-lint.per-file-ignores]
                "/scrapinghub.yml" = ["SCP01", "SCP18"]  # why
                "/requirements.txt" = ["SCP13"]
                """,
            )
            + "\n",
        ),
    ],
)
def test_add_ignore_file_level(capsys, pyproject, expected):
    """Issues about a file as a whole are ignored with per-file ignores."""
    files = [*FILE_LEVEL_PROJECT]
    if pyproject is not None:
        files.append(File(pyproject, path="pyproject.toml"))
    with project(files):
        main(["--add-ignore"])
        assert Path("pyproject.toml").read_text(encoding="utf-8") == expected
        main([])
    out, _ = capsys.readouterr()
    assert out == "Ignored 2 error(s).\n"


def test_add_ignore_fix(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["--add-ignore", "--fix"])
    _, err = capsys.readouterr()
    assert "not allowed with argument" in err
    assert excinfo.value.code == 2
