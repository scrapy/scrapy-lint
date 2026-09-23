from __future__ import annotations

import re
from ast import AsyncFunctionDef, ClassDef, FunctionDef, Name, Store, alias, parse, walk
from collections import defaultdict
from configparser import ConfigParser
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING, Any

from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.utils import canonicalize_name
from packaging.version import Version
from pathspec import GitIgnoreSpec
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

try:
    import tomllib  # type: ignore[import-not-found]
except ImportError:  # Python < 3.11
    import tomli as tomllib

from scrapy_lint.errors import InputFileError
from scrapy_lint.requirements import iter_requirement_lines

if TYPE_CHECKING:
    from collections.abc import Generator, Sequence

    from packaging.requirements import Requirement

    from scrapy_lint.issues import Issue

_STACK_IMAGE = re.compile(
    r"\s*FROM\s+(?P<image>(?:\S+/)?scrapinghub-stack-[^\s:]+(?::(?P<tag>\S+))?)",
    re.IGNORECASE,
)


def _defines(module_file: Path, name: str) -> bool:
    try:
        tree = parse(module_file.read_text(encoding="utf-8"))
    except (OSError, SyntaxError, UnicodeDecodeError, ValueError):
        return True
    # Nested nodes also count, so that a name defined within a conditional
    # import or a function body does not read as missing.
    for node in walk(tree):
        if isinstance(node, alias):
            if node.name == "*" or (node.asname or node.name.split(".")[0]) == name:
                return True
        elif isinstance(node, (AsyncFunctionDef, ClassDef, FunctionDef)):
            if node.name == name:
                return True
        elif isinstance(node, Name) and isinstance(node.ctx, Store) and node.id == name:
            return True
    return False


@dataclass
class PythonDeclaration:
    """Python version that a project declares, and where it declares it."""

    key: str
    value: str
    specifier: SpecifierSet
    file: Path


@dataclass
class Project:
    path: Path

    @cached_property
    def dockerfile(self) -> Path | None:
        """Dockerfile that Scrapy Cloud builds to deploy this project."""
        if _find_image(self.scrapy_cloud_config) is not True:
            return None
        path = self.path / "Dockerfile"
        if not path.exists():
            return None
        return path.resolve()

    @cached_property
    def dockerfile_stacks(self) -> list[tuple[int, int, str]]:
        """Line, column and tag of every stack image the Dockerfile builds on."""
        if not self.dockerfile:
            return []
        text = self.dockerfile.read_text(encoding="utf-8", errors="ignore")
        return list(_iter_stack_images(text))

    @cached_property
    def frozen_requirements(self) -> dict[str, Version]:
        result = {}
        for name, requirements in self._requirements.items():
            for requirement in requirements:
                if len(requirement.specifier) != 1:
                    continue
                spec = next(iter(requirement.specifier))
                if spec.operator != "==":
                    continue
                result[name] = Version(spec.version)
        return result

    @cached_property
    def scrapy_lint_options(self) -> dict[str, Any]:
        return self._pyproject.get("tool", {}).get("scrapy-lint", {})

    @cached_property
    def declared_python(self) -> PythonDeclaration | None:
        """Return the Python version that the project declares.

        Declarations are looked up in the :file:`.python-version` file and in
        the ``requires-python`` key of :file:`pyproject.toml`, in that order.
        The result is ``None`` when neither declares a valid Python version.
        """
        python_version_path = self.path / ".python-version"
        version = _read_python_version_file(python_version_path)
        if version is not None:
            return _declaration(
                ".python-version",
                version,
                python_version_path,
                exact=True,
            )
        specifier = self._pyproject.get("project", {}).get("requires-python")
        if not isinstance(specifier, str):
            return None
        return _declaration(
            "requires-python",
            specifier,
            self.path / "pyproject.toml",
        )

    @cached_property
    def packages(self) -> set[str]:
        packages = set(self._requirements)
        # The package that a code base defines is not among its requirements,
        # but it is available to it. An empty set means that no requirements
        # are declared, i.e. that nothing is known about available packages.
        name = self._pyproject.get("project", {}).get("name")
        if packages and isinstance(name, str):
            packages.add(canonicalize_name(name))
        return packages

    @cached_property
    def requirements_file(self) -> Path | None:
        requirements_file: Path | None
        path_str = self.scrapy_lint_options.get("requirements_file")
        if path_str is not None:
            requirements_file = Path(path_str).resolve()
            if requirements_file.exists():
                return requirements_file

        # Check scrapinghub.yml for requirements file
        if self.scrapy_cloud_config:
            try:
                requirements_file_name = self.scrapy_cloud_config.get(
                    "requirements", {}
                ).get(
                    "file",
                    "",
                )
            except AttributeError:
                pass
            else:
                if requirements_file_name and isinstance(
                    requirements_file_name,
                    str,
                ):
                    scrapinghub_requirements_file = Path(requirements_file_name)
                    if scrapinghub_requirements_file.exists():
                        return scrapinghub_requirements_file.resolve()

        # Fall back to requirements.txt
        requirements_file = Path("requirements.txt")
        if requirements_file.exists():
            return requirements_file.resolve()

        return None

    @cached_property
    def requirements_text(self) -> str | None:
        if not self.requirements_file or not self.requirements_file.exists():
            return None

        try:
            return self.requirements_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return None

    @cached_property
    def scrapy_cloud_config(self) -> dict[str, Any] | None:
        config_file = self.path / "scrapinghub.yml"
        if not config_file.exists():
            return None
        yaml_parser = YAML(typ="safe")
        try:
            with config_file.open(encoding="utf-8") as f:
                return yaml_parser.load(f)
        except (UnicodeDecodeError, YAMLError):
            return None

    @cached_property
    def setting_module_paths(self) -> set[Path]:
        config_file = self.path / "scrapy.cfg"
        config = ConfigParser()
        config.read(config_file)
        if "settings" not in config:
            return set()
        result = set()
        for module_path in config["settings"].values():
            parts = module_path.split(".")
            pkg_path = self.path.joinpath(*parts, "__init__.py")
            if pkg_path.exists():
                result.add(pkg_path)
                continue
            mod_path = self.path.joinpath(*parts[:-1], f"{parts[-1]}.py")
            if mod_path.exists():
                result.add(mod_path)
        return result

    def is_missing_import_path(self, path: str) -> bool:
        """Return whether *path* names a module or object missing from this
        project.

        Paths that start outside this project, and paths that cannot be
        resolved with certainty, count as present.
        """
        parts = path.split(".")
        for index in range(len(parts), 0, -1):
            module_file = self._module_file(parts[:index])
            if module_file is None:
                # A directory without __init__.py may be a namespace package
                # extending beyond this project.
                if self.path.joinpath(*parts[:index]).is_dir():
                    break
                continue
            if index == len(parts):
                break
            return not _defines(module_file, parts[index])
        return False

    def _module_file(self, parts: Sequence[str]) -> Path | None:
        base = self.path.joinpath(*parts)
        for candidate in (base / "__init__.py", base.with_suffix(".py")):
            if candidate.is_file():
                return candidate
        return None

    @cached_property
    def _pyproject(self) -> dict[str, Any]:
        pyproject_path = self.path / "pyproject.toml"
        if not pyproject_path.exists():
            return {}
        try:
            return tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
        except (tomllib.TOMLDecodeError, UnicodeDecodeError) as e:
            raise InputFileError(str(e), pyproject_path) from None

    @cached_property
    def _pyproject_requirements(self) -> list[str]:
        metadata = self._pyproject.get("project", {})
        groups = [metadata.get("dependencies", [])]
        groups.extend(metadata.get("optional-dependencies", {}).values())
        return [line for group in groups for line in group if isinstance(line, str)]

    @cached_property
    def uses_stack(self) -> bool:
        """Whether the project is deployed on a Zyte stack."""
        config = self.scrapy_cloud_config
        if _find_image(config) is not False:
            return bool(self.dockerfile_stacks)
        return _has_stack(config)

    @cached_property
    def _requirements(self) -> dict[str, list[Requirement]]:
        content = self.requirements_text
        lines = (
            self._pyproject_requirements if content is None else content.splitlines()
        )
        result = defaultdict(list)
        for _, name, requirement in iter_requirement_lines(lines):
            result[name].append(requirement)
        return result


def _declaration(
    key: str,
    value: str,
    file: Path,
    exact: bool = False,
) -> PythonDeclaration | None:
    """Return the declaration that *value* makes, ``None`` if it is invalid.

    *value* is a version when *exact* is true, and a version specifier
    otherwise.
    """
    try:
        specifier = SpecifierSet(f"=={value}" if exact else value)
    except InvalidSpecifier:
        return None
    return PythonDeclaration(key, value, specifier, file)


def _read_python_version_file(path: Path) -> str | None:
    """Return the version in a :file:`.python-version` file."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    for line in text.splitlines():
        version = line.strip()
        if version and not version.startswith("#"):
            return version
    return None


@dataclass
class Context:
    project: Project

    @property
    def options(self) -> dict[str, Any]:
        return self.project.scrapy_lint_options

    @cached_property
    def ignores(self) -> set[int]:
        return {int(code[3:]) for code in self.options.get("ignore", [])}

    @cached_property
    def per_file_ignores(self) -> list[tuple[GitIgnoreSpec, set[int]]]:
        return [
            (
                GitIgnoreSpec.from_lines([pattern]),
                {int(code[3:]) for code in codes},
            )
            for pattern, codes in self.options.get("per-file-ignores", {}).items()
        ]

    def is_ignored(self, issue: Issue, file: Path) -> bool:
        """Return whether *issue* must be silenced, given *file*, its path
        relative to the project root."""
        return issue.code in self.ignores or any(
            issue.code in codes and spec.match_file(file)
            for spec, codes in self.per_file_ignores
        )


def _iter_stack_images(text: str) -> Generator[tuple[int, int, str]]:
    for line_number, line in enumerate(text.splitlines(), start=1):
        match = _STACK_IMAGE.match(line)
        if match:
            yield line_number, match.start("image"), match.group("tag") or ""


def _find_image(data: Any) -> Any:
    """Return the value of the first ``image`` key in *data*, or ``False``."""
    if isinstance(data, dict):
        if "image" in data:
            return data["image"]
        for value in data.values():
            result = _find_image(value)
            if result is not False:
                return result
    return False


def _has_stack(data: Any) -> bool:
    if isinstance(data, dict):
        if "stack" in data or "stacks" in data:
            return True
        return any(_has_stack(value) for value in data.values())
    return False
