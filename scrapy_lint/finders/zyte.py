from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from packaging.version import Version
from ruamel.yaml import YAML, CommentedMap
from ruamel.yaml.error import YAMLError

from scrapy_lint._python import allowed_series, end_of_life, stack_python
from scrapy_lint.context import _find_image
from scrapy_lint.data.stacks import LATEST_STACK_SCRAPY_VERSION
from scrapy_lint.issues import (
    EOL_PYTHON,
    HARDCODED_SECRET,
    INVALID_SCRAPINGHUB_YML,
    NO_ROOT_REQUIREMENTS,
    NO_ROOT_STACK,
    NON_ROOT_REQUIREMENTS,
    NON_ROOT_STACK,
    REQUIREMENTS_FILE_MISMATCH,
    SCRAPY_VERSION_MISMATCH,
    STACK_NOT_FROZEN,
    STACK_PYTHON_MISMATCH,
    UNEXISTING_REQUIREMENTS_FILE,
    Issue,
    Pos,
)

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

    from scrapy_lint.context import Context

_STACK_SCRAPY_VERSION = re.compile(r"scrapy:(?P<version>\d+\.\d+)")


def _key_position(data: CommentedMap, key: str) -> Pos:
    line, column = data.lc.key(key)
    return Pos(line + 1, column)


def _value_position(data: CommentedMap, key: str) -> Pos:
    line, column = data.lc.value(key)
    return Pos(line + 1, column)


class ZyteCloudConfigIssueFinder:
    def __init__(self, context: Context):
        self.context = context

    def lint(self, file: Path) -> Generator[Issue]:
        yaml_parser = YAML(typ="rt")
        try:
            data = yaml_parser.load(file.read_text(encoding="utf-8"))
        except YAMLError as e:
            yield Issue(INVALID_SCRAPINGHUB_YML, detail=str(e))
            return
        if not isinstance(data, CommentedMap):
            detail = "non-mapping root data structure"
            yield Issue(INVALID_SCRAPINGHUB_YML, detail=detail)
            return
        if "apikeys" in data:
            pos = _key_position(data, "apikeys")
            yield Issue(HARDCODED_SECRET, pos, "apikeys")
        # Scrapy Cloud ignores the stack and requirements keys of projects
        # deployed as a custom image, only their validity still matters.
        image = bool(_find_image(data))
        if not image:
            if "stack" not in data and not self._has_stacks_default(data):
                yield Issue(NO_ROOT_STACK)
            if "requirements" not in data:
                yield Issue(NO_ROOT_REQUIREMENTS)
        yield from self.check_keys(data, image=image)

    def check_keys(
        self,
        data: CommentedMap,
        is_root: bool = True,
        image: bool = False,
    ) -> Generator[Issue]:
        for key, value in data.items():
            if key == "stack" and not image:
                if not is_root:
                    yield Issue(NON_ROOT_STACK, _key_position(data, key))
                yield from self._check_stack_value(data, key)
            elif key == "requirements":
                if not is_root and not image:
                    pos = _key_position(data, key)
                    yield Issue(NON_ROOT_REQUIREMENTS, pos)
                pos = _value_position(data, key)
                yield from self._check_requirements_value(value, pos)
            elif key == "stacks" and is_root and not image:
                if not isinstance(value, CommentedMap):
                    pos = _value_position(data, key)
                    yield Issue(INVALID_SCRAPINGHUB_YML, pos, "non-mapping stacks")
                else:
                    for stack_key in value:
                        pos = _key_position(value, stack_key)
                        yield Issue(NON_ROOT_STACK, pos)
                        yield from self._check_stack_value(value, stack_key)
            if isinstance(value, CommentedMap):
                yield from self.check_keys(value, is_root=False, image=image)

    def _check_stack_value(self, data: CommentedMap, key: str) -> Generator[Issue]:
        value = data[key]
        pos = _value_position(data, key)
        if not isinstance(value, str):
            yield Issue(INVALID_SCRAPINGHUB_YML, pos, "non-str stack")
            return
        if not re.search(r"-\d{8}$", value):
            yield Issue(STACK_NOT_FROZEN, pos)
        yield from self._check_stack_scrapy_version(value, pos)
        yield from self._check_stack_python(value, pos)

    def _check_stack_scrapy_version(self, value: str, pos: Pos) -> Generator[Issue]:
        match = _STACK_SCRAPY_VERSION.match(value)
        frozen = self.context.project.frozen_requirements.get("scrapy")
        if not match or frozen is None:
            return
        stack_version = Version(match["version"])
        frozen_version = Version(f"{frozen.major}.{frozen.minor}")
        if frozen_version == stack_version:
            return
        # A newer Scrapy than the newest stack is the only way to use a Scrapy
        # release for which no stack exists yet.
        if frozen_version > stack_version >= LATEST_STACK_SCRAPY_VERSION:
            return
        detail = f"{value} comes with Scrapy {stack_version}, not {frozen}"
        yield Issue(SCRAPY_VERSION_MISMATCH, pos, detail)

    def _check_stack_python(self, stack: str, pos: Pos) -> Generator[Issue]:
        python = stack_python(stack)
        if python is None:
            return
        eol = end_of_life(python)
        if eol is not None:
            detail = f"stack Python {python} reached its end of life on {eol}"
            yield Issue(EOL_PYTHON, pos, detail)
        declaration = self.context.project.declared_python
        if declaration is None:
            return
        series = allowed_series(declaration.specifier)
        if series and python not in series:
            detail = (
                f"stack Python {python} does not match "
                f"{declaration.key} ({declaration.value})"
            )
            yield Issue(STACK_PYTHON_MISMATCH, pos, detail)

    def _check_requirements_value(
        self,
        requirements_value: Any,
        pos: Pos,
    ) -> Generator[Issue]:
        if not isinstance(requirements_value, CommentedMap):
            yield Issue(INVALID_SCRAPINGHUB_YML, pos, "non-mapping requirements")
            return

        if "file" not in requirements_value:
            yield Issue(INVALID_SCRAPINGHUB_YML, pos, "no requirements.file key")
            return

        file_value = requirements_value["file"]
        pos = _value_position(requirements_value, "file")
        if not isinstance(file_value, str):
            yield Issue(INVALID_SCRAPINGHUB_YML, pos, "non-str requirements.file")
            return
        if not file_value.strip():
            yield Issue(INVALID_SCRAPINGHUB_YML, pos, "empty requirements.file")
            return

        if self.context.project.path:
            requirements_path = self.context.project.path / file_value
            if not requirements_path.exists():
                yield Issue(UNEXISTING_REQUIREMENTS_FILE, pos)
            elif (
                self.context.project.requirements_file
                and requirements_path != self.context.project.requirements_file
            ):
                yield Issue(REQUIREMENTS_FILE_MISMATCH, pos)

    def _has_stacks_default(self, data: CommentedMap) -> bool:
        return (
            "stacks" in data
            and isinstance(data["stacks"], CommentedMap)
            and "default" in data["stacks"]
        )
