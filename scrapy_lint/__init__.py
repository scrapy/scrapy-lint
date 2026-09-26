from __future__ import annotations

import os
import sys
from argparse import ArgumentParser
from pathlib import Path
from typing import TYPE_CHECKING

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
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument(
        "--fix",
        action="store_true",
        help=("Apply available automatic fixes and report the remaining issues."),
    )
    actions.add_argument(
        "--add-ignore",
        action="store_true",
        help="Add ignore comments for all issues and report the remaining ones.",
    )
    return parser


def _build_linter(args: Sequence[str]) -> tuple[Namespace, Linter]:
    parsed_args = get_parser().parse_args(args)
    return parsed_args, Linter.from_args(parsed_args)


def lint(args: Sequence[str]) -> Generator[Issue]:
    _, linter = _build_linter(args)
    yield from linter.lint()


_BOLD = "1"
_RED = "31"
_CYAN = "36"


def _colors_enabled() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return sys.stdout.isatty()


def _style(text: str, color: str) -> str:
    if not _colors_enabled():
        return text
    return f"\033[{color}m{text}\033[0m"


def _report(issue: Issue) -> str:
    location = _style(issue.location, _BOLD)
    rule = _style(issue.rule, _RED)
    marker = f" {_style('[*]', _CYAN)}" if issue.fix is not None else ""
    return f"{location}: {rule} {issue.description}{marker}"


def main(args: Sequence[str] | None = None) -> None:
    args = args if args is not None else sys.argv[1:]
    try:
        parsed_args, linter = _build_linter(args)
        if parsed_args.fix or parsed_args.add_ignore:
            result = linter.fix() if parsed_args.fix else linter.add_ignores()
            for issue in result.remaining:
                print(_report(issue))
            if result.fixed_count:
                verb = "Fixed" if parsed_args.fix else "Ignored"
                print(f"{verb} {result.fixed_count} error(s).")
            if result.remaining:
                sys.exit(1)
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
            marker = _style("[*]", _CYAN)
            print(f"{marker} {fixable} fixable with the `--fix` option.")
        if found_issues:
            sys.exit(1)
