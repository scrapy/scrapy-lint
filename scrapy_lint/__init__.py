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
    parser.add_argument(
        "--fix",
        action="store_true",
        help=("Apply available automatic fixes and report the remaining issues."),
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
    location = _style(f"{issue.file}:{issue.line}:{issue.column}", _BOLD)
    code = _style(f"SCP{issue.code:02}", _RED)
    detail = f": {issue.detail}" if issue.detail else ""
    marker = f" {_style('[*]', _CYAN)}" if issue.fix is not None else ""
    return f"{location}: {code} {issue.summary}{detail}{marker}"


def main(args: Sequence[str] | None = None) -> None:
    args = args if args is not None else sys.argv[1:]
    try:
        parsed_args, linter = _build_linter(args)
        if parsed_args.fix:
            result = linter.fix()
            for issue in result.remaining:
                print(_report(issue))
            if result.fixed_count:
                print(f"Fixed {result.fixed_count} error(s).")
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
