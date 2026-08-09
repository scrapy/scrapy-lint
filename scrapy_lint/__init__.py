from __future__ import annotations

import sys
from argparse import ArgumentParser
from pathlib import Path
from typing import TYPE_CHECKING

from . import cloud
from .errors import CloudError
from .linter import InputFileError, Linter

if TYPE_CHECKING:
    from argparse import Namespace
    from collections.abc import Generator, Sequence

    from .issues import Issue


def get_parser() -> ArgumentParser:
    parser = ArgumentParser(
        epilog="Run `scrapy-lint cloud --help` for Scrapy Cloud checks.",
    )
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


def _report(issue: Issue) -> str:
    marker = " [*]" if issue.fix is not None else ""
    return f"{issue}{marker}"


def get_cloud_parser() -> ArgumentParser:
    return ArgumentParser(prog="scrapy-lint cloud")


def _main_cloud(args: Sequence[str]) -> None:
    get_cloud_parser().parse_args(args)
    found_issues = False
    try:
        for issue in cloud.check():
            found_issues = True
            print(issue)
    except (CloudError, InputFileError) as e:
        print(e, file=sys.stderr)
        sys.exit(2)
    if found_issues:
        sys.exit(1)


def main(args: Sequence[str] | None = None) -> None:
    args = args if args is not None else sys.argv[1:]
    if args and args[0] == "cloud":
        _main_cloud(args[1:])
        return
    try:
        parsed_args, linter = _build_linter(args)
        if parsed_args.fix:
            result = linter.fix()
            for issue in result.remaining:
                print(issue)
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
            print(f"[*] {fixable} fixable with the `--fix` option.")
        if found_issues:
            sys.exit(1)
