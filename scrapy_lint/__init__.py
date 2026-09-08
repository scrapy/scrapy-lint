from __future__ import annotations

import sys
from argparse import ArgumentParser
from pathlib import Path
from typing import TYPE_CHECKING

from .issues import UNKNOWN_SETTING
from .linter import InputFileError, Linter

if TYPE_CHECKING:
    from argparse import Namespace
    from collections.abc import Generator, Sequence

    from .issues import Issue


def get_parser() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument(
        "paths",
        type=Path,
        nargs="*",
        default=[Path().cwd()],
        metavar="FILES",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--fix",
        action="store_true",
        help=("Apply available automatic fixes and report the remaining issues."),
    )
    group.add_argument(
        "--add-known-settings",
        action="store_true",
        help=(
            "Add every unknown setting to the known-settings option of "
            "pyproject.toml, and report the remaining issues."
        ),
    )
    return parser


def _build_linter(args: Sequence[str]) -> tuple[Namespace, Linter]:
    parsed_args = get_parser().parse_args(args)
    return parsed_args, Linter.from_args(parsed_args)


def lint(args: Sequence[str]) -> Generator[Issue]:
    _, linter = _build_linter(args)
    yield from linter.lint()


def _report(issue: Issue) -> str:
    marker = " [*]" if issue.fix is not None else ""
    return f"{issue}{marker}"


def _add_known_settings(linter: Linter) -> None:
    remaining = [issue for issue in linter.lint() if issue.code != UNKNOWN_SETTING[0]]
    added = linter.project.add_known_settings(linter.setting_checker.unknown_settings)
    for issue in remaining:
        print(issue)
    if added:
        print(f"Added {len(added)} setting(s) to known-settings.")
    if remaining:
        sys.exit(1)


def _fix(linter: Linter) -> None:
    result = linter.fix()
    for issue in result.remaining:
        print(issue)
    if result.fixed_count:
        print(f"Fixed {result.fixed_count} error(s).")
    if result.remaining:
        sys.exit(1)


def main(args: Sequence[str] | None = None) -> None:
    args = args if args is not None else sys.argv[1:]
    try:
        parsed_args, linter = _build_linter(args)
        if parsed_args.add_known_settings:
            _add_known_settings(linter)
            return
        if parsed_args.fix:
            _fix(linter)
            return
        fixable = 0
        found_issues = False
        for issue in linter.lint():
            found_issues = True
            fixable += issue.fix is not None
            print(_report(issue))
    except InputFileError as e:
        print(e, file=sys.stderr)
        sys.exit(2)
    else:
        if fixable:
            print(f"[*] {fixable} fixable with the `--fix` option.")
        if found_issues:
            sys.exit(1)
