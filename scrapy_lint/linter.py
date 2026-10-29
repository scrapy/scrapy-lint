from __future__ import annotations

import ast
import re
import warnings
from ast import NodeVisitor
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

import tomlkit
from pathspec import GitIgnoreSpec

from scrapy_lint.fixes import apply_edits
from scrapy_lint.issues import Issue

from ._ignore_comments import (
    IgnoreComments,
    preceding_ignore_comments,
    python_ignore_comments,
    trailing_ignore_comments,
)
from .context import Context, Project
from .errors import InputFileError
from .finders.apis import APIIssueFinder
from .finders.attributes import SpiderAttributeIssueFinder
from .finders.dockerfile import find_dockerfile_issues
from .finders.domains import (
    UnreachableDomainIssueFinder,
    UrlInAllowedDomainsIssueFinder,
    find_no_allowed_domains_issues,
)
from .finders.imports import ImportIssueFinder
from .finders.items import DocumentationCommentIssueFinder
from .finders.loggers import SpiderLoggerIssueFinder
from .finders.methods import DeprecatedArgumentIssueFinder
from .finders.oldstyle import (
    ExtractIssueFinder,
    OldSelectorIssueFinder,
    UrlparseIssueFinder,
    find_absolute_nested_xpath_issues,
    find_get_first_by_index_issues,
    find_url_join_issues,
)
from .finders.python_version import PythonVersionIssueFinder
from .finders.requests import RequestIssueFinder
from .finders.requirements import RequirementsIssueFinder
from .finders.settings import (
    SettingChecker,
    SettingIssueFinder,
    SettingModuleIssueFinder,
)
from .finders.spiders import StartUrlIssueFinder, UnneededStartIssueFinder
from .finders.unsupported import LambdaCallbackIssueFinder
from .finders.zyte import ZyteCloudConfigIssueFinder

if TYPE_CHECKING:
    from argparse import Namespace
    from collections.abc import Generator, Sequence

    from .issues import Issue


class IssueFinder(Protocol):  # pylint: disable=too-few-public-methods
    def __call__(self, node: ast.AST) -> Generator[Issue]: ...


class PythonIssueFinder(NodeVisitor):
    def __init__(
        self,
        context: Context,
        setting_checker: SettingChecker,
        source: str,
        tree: ast.Module,
    ):
        super().__init__()
        self.issues: list[Issue] = []
        api_issue_finder = APIIssueFinder(context, source)
        domain_issue_finder = UnreachableDomainIssueFinder()
        lambda_callback_issue_finder = LambdaCallbackIssueFinder()
        setting_issue_finder = SettingIssueFinder(setting_checker)
        extract_issue_finder = ExtractIssueFinder()
        spider_logger_issue_finder = SpiderLoggerIssueFinder()
        import_issue_finder = ImportIssueFinder(setting_checker.project, source)

        self.finders: dict[str, Sequence[IssueFinder]] = {
            "Assign": [
                lambda_callback_issue_finder,
                OldSelectorIssueFinder(),
                setting_issue_finder,
                domain_issue_finder,
                UrlInAllowedDomainsIssueFinder(source),
                spider_logger_issue_finder,
            ],
            "AugAssign": [
                setting_issue_finder,
            ],
            "Call": [
                extract_issue_finder,
                find_absolute_nested_xpath_issues,
                find_get_first_by_index_issues,
                lambda_callback_issue_finder,
                api_issue_finder,
                RequestIssueFinder(),
                setting_issue_finder,
                find_url_join_issues,
                UrlparseIssueFinder(tree, source),
            ],
            "ClassDef": [
                api_issue_finder,
                domain_issue_finder,
                find_no_allowed_domains_issues,
                StartUrlIssueFinder(source),
                spider_logger_issue_finder,
                UnneededStartIssueFinder(source),
                SpiderAttributeIssueFinder(context),
                DeprecatedArgumentIssueFinder(context),
                DocumentationCommentIssueFinder(source),
            ],
            "Compare": [
                setting_issue_finder,
            ],
            "FunctionDef": [
                setting_issue_finder,
            ],
            "Import": [
                import_issue_finder,
            ],
            "ImportFrom": [
                import_issue_finder,
            ],
            "Subscript": [
                extract_issue_finder,
                setting_issue_finder,
            ],
        }
        self.post_visitors = {
            "FunctionDef": (setting_issue_finder,),
        }

    def find_issues_visitor(self, visitor, node):
        """Find issues for the provided visitor"""
        for finder in self.finders[visitor]:
            issues = finder(node)
            if issues:
                self.issues.extend(list(issues))
        self.generic_visit(node)
        for finder in self.post_visitors.get(visitor, ()):
            assert hasattr(finder, "post_visit")
            finder.post_visit(node)

    def visit(self, node):
        node_type = type(node).__name__
        if node_type in self.finders:
            self.find_issues_visitor(node_type, node)
        else:
            super().visit(node)


@dataclass
class FixResult:
    fixed_count: int = 0
    remaining: list[Issue] = field(default_factory=list)


class Linter:
    @classmethod
    def from_args(cls, args: Namespace) -> Linter:
        return cls(args.paths, fix=getattr(args, "fix", False))

    def __init__(self, paths: Sequence[Path], fix: bool = False) -> None:
        self.fix_enabled = fix
        self.project = Project(Path().cwd())
        self.context = Context(self.project)
        self.files = self.resolve_files(self.project, paths)
        self.setting_checker = SettingChecker(self.context)
        self.ignores: set[int] = {
            int(code[3:]) for code in self.project.scrapy_lint_options.get("ignore", [])
        }
        self.per_file_ignores: list[tuple[GitIgnoreSpec, set[int]]] = [
            (
                GitIgnoreSpec.from_lines([pattern]),
                {int(code[3:]) for code in codes},
            )
            for pattern, codes in self.project.scrapy_lint_options.get(
                "per-file-ignores", {}
            ).items()
        ]

    @classmethod
    def resolve_files(
        cls,
        project: Project,
        paths: Sequence[Path],
    ) -> Sequence[Path]:
        files = set()
        spec = None
        gitignore = project.path / ".gitignore"
        if gitignore.exists():
            spec = GitIgnoreSpec.from_lines(
                gitignore.read_text(encoding="utf-8").splitlines(),
            )
        for path in paths:
            if path.is_file():
                files.add(path)
                continue
            if path.resolve() == project.path:
                zyte_config_path = project.path / "scrapinghub.yml"
                if zyte_config_path.exists():
                    files.add(zyte_config_path)
                for name in ("pyproject.toml", ".python-version"):
                    declaration_path = project.path / name
                    if declaration_path.exists():
                        files.add(declaration_path)
                if project.requirements_file and project.requirements_file.exists():
                    files.add(project.requirements_file)
                if project.dockerfile:
                    files.add(project.dockerfile)
            for python_file_path in path.glob("**/*.py"):
                if spec is None or not spec.match_file(
                    python_file_path.relative_to(project.path),
                ):
                    files.add(python_file_path)
        return sorted(files)

    def lint(self) -> Generator[Issue]:
        for file in self.files:
            absolute_file = file.resolve()
            relative_file = absolute_file.relative_to(self.project.path)
            ignore_comments: IgnoreComments | None = None
            for issue in self.lint_file(absolute_file):
                if self.is_ignored(issue, relative_file):
                    continue
                if ignore_comments is None:
                    ignore_comments = self._ignore_comments(absolute_file)
                if ignore_comments.ignores(issue):
                    continue
                issue.file = relative_file
                yield issue

    def fix(self) -> FixResult:
        result = FixResult()
        fixes_by_file: dict[Path, list[Issue]] = {}
        for issue in self.lint():
            if issue.fix is None:
                result.remaining.append(issue)
                continue
            assert issue.file is not None
            absolute_file = (self.project.path / issue.file).resolve()
            fixes_by_file.setdefault(absolute_file, []).append(issue)
        for file, issues in fixes_by_file.items():
            edits = [edit for issue in issues for edit in issue.fix.edits]  # type: ignore[union-attr]
            source = file.read_text(encoding="utf-8")
            new_source, applied = apply_edits(source, edits)
            if applied:
                file.write_text(new_source, encoding="utf-8")
            result.fixed_count += sum(
                all(edit in applied for edit in issue.fix.edits)  # type: ignore[union-attr]
                for issue in issues
            )
        return result

    def add_ignores(self) -> FixResult:
        """Ignore every issue, with ignore comments or, for issues about a
        file as a whole, with :ref:`per-file-ignores`."""
        result = FixResult()
        issues_by_file: dict[Path, list[Issue]] = {}
        file_level_rules: dict[Path, set[str]] = {}
        for issue in self.lint():
            assert issue.file is not None
            result.fixed_count += 1
            if issue._file_level:  # pylint: disable=protected-access
                file_level_rules.setdefault(issue.file, set()).add(issue.rule)
                continue
            absolute_file = (self.project.path / issue.file).resolve()
            issues_by_file.setdefault(absolute_file, []).append(issue)
        for file, issues in issues_by_file.items():
            source = file.read_text(encoding="utf-8")
            edits = self._ignore_comments(file).edits(issues)
            new_source, _ = apply_edits(source, edits)
            file.write_text(new_source, encoding="utf-8")
        if file_level_rules:
            self._add_per_file_ignores(file_level_rules)
        return result

    def _add_per_file_ignores(self, rules_by_file: dict[Path, set[str]]) -> None:
        path = self.project.path / "pyproject.toml"
        document = (
            tomlkit.parse(path.read_text(encoding="utf-8"))
            if path.exists()
            else tomlkit.document()
        )
        tool = document.setdefault("tool", tomlkit.table(is_super_table=True))
        options = tool.setdefault("scrapy-lint", tomlkit.table(is_super_table=True))
        per_file_ignores = options.setdefault("per-file-ignores", tomlkit.table())
        for file, rules in sorted(rules_by_file.items()):
            pattern = "/" + re.sub(r"([*?[\\])", r"\\\1", file.as_posix())
            codes = per_file_ignores.setdefault(pattern, tomlkit.array())
            codes.extend(sorted(rules - set(codes)))
        path.write_text(tomlkit.dumps(document), encoding="utf-8")

    def _ignore_comments(self, file: Path) -> IgnoreComments:
        source = file.read_text(encoding="utf-8")
        if file.suffix == ".py":
            return python_ignore_comments(source)
        if file.name == ".python-version":
            return preceding_ignore_comments(source)
        if file == self.project.dockerfile:
            return preceding_ignore_comments(source, dockerfile=True)
        return trailing_ignore_comments(source)

    def is_ignored(self, issue: Issue, file: Path) -> bool:
        return issue.code in self.ignores or any(
            issue.code in codes and spec.match_file(file)
            for spec, codes in self.per_file_ignores
        )

    def lint_file(self, file: Path) -> Generator[Issue]:
        if file.suffix == ".py":
            yield from self.lint_python_file(file)
        elif file.name == "scrapinghub.yml":
            yield from ZyteCloudConfigIssueFinder(self.context).lint(file)
        elif file.name in {"pyproject.toml", ".python-version"}:
            yield from PythonVersionIssueFinder(self.context).lint(file)
        elif file == self.project.dockerfile:
            yield from find_dockerfile_issues(self.context)
        elif (
            self.project.requirements_file is not None
            and file == self.project.requirements_file
        ):
            yield from RequirementsIssueFinder(self.context).lint(file)

    def lint_python_file(self, file: Path) -> Generator[Issue]:
        try:
            with file.open("r", encoding="utf-8") as f:
                source = f.read()
        except UnicodeDecodeError as e:
            raise InputFileError(str(e), file) from None
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            try:
                tree = ast.parse(source, filename=str(file))
            except SyntaxError as e:
                raise InputFileError(str(e), file) from None
        self.setting_checker.source = source
        setting_module_finder = SettingModuleIssueFinder(
            self.context,
            file,
            self.setting_checker,
        )
        if file in self.context.project.setting_module_paths:
            yield from setting_module_finder.check(tree)
        finder = PythonIssueFinder(self.context, self.setting_checker, source, tree)
        finder.visit(tree)
        yield from finder.issues
