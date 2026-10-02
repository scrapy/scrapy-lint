from __future__ import annotations

from ast import (
    AST,
    Assign,
    Attribute,
    AugAssign,
    Call,
    ClassDef,
    Compare,
    Constant,
    Dict,
    FunctionDef,
    Import,
    ImportFrom,
    In,
    Module,
    Name,
    NodeVisitor,
    NotIn,
    Subscript,
    expr,
)
from contextlib import suppress
from typing import TYPE_CHECKING, Any

from packaging.version import Version

from scrapy_lint.ast import (
    definition_column,
    extract_literal_value,
    import_column,
    is_dict,
    iter_dict,
)
from scrapy_lint.data.addons import ADDONS
from scrapy_lint.data.settings import SETTINGS
from scrapy_lint.finders.zyte_api import PARAM_SETTINGS, find_param_issues
from scrapy_lint.issues import (
    IMPORTED_SETTING,
    IMPROPER_SETTING_DEFINITION,
    INCOMPLETE_PROJECT_THROTTLING,
    LOW_PROJECT_THROTTLING,
    MISSING_CHANGING_SETTING,
    NO_PROJECT_USER_AGENT,
    REDEFINED_SETTING,
    REDUNDANT_SETTING_VALUE,
    ROBOTS_TXT_IGNORED_BY_DEFAULT,
    SESSION_ROTATION,
    UNNEEDED_SETTING_GET,
    WRONG_ADDON_ORDER,
    Issue,
    Pos,
)
from scrapy_lint.settings import (
    MAX_DEFAULT_VALUE_HISTORY,
    SETTING_METHODS,
    SETTING_SETTERS,
    UNKNOWN_SETTING_VALUE,
    UnknownSettingValue,
    getbool,
)
from scrapy_lint.versions import UNKNOWN_FUTURE_VERSION, UNKNOWN_UNSUPPORTED_VERSION

from .checker import SESSION_SETTINGS, LineNumber, SettingChecker

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

    from scrapy_lint.context import Context

    from .checker import AddonEntry


class SettingIssueFinder:
    NON_METHOD_SETTINGS_CALLABLES = ("BaseSettings", "Settings", "overridden_settings")

    def __init__(self, setting_checker: SettingChecker):
        self.setting_checker = setting_checker

    def __call__(
        self,
        node: AST,
    ) -> Generator[Issue]:
        if isinstance(node, Call):
            yield from self.find_call_issues(node)
            return
        if isinstance(node, Assign):
            yield from self.find_assign_issues(node)
            return
        if isinstance(node, AugAssign):
            yield from self.find_aug_assign_issues(node)
            return
        if isinstance(node, Subscript):
            yield from self.find_subscript_issues(node)
            return
        if isinstance(node, Compare):
            yield from self.find_compare_issues(node)
            return
        if isinstance(node, FunctionDef):
            if node.name == "update_pre_crawler_settings":
                self.setting_checker.in_update_pre_crawler_settings = True
            elif node.name == "update_settings":
                self.setting_checker.in_update_settings = True
            return

    def post_visit(self, node: Call | Compare | FunctionDef | Subscript) -> None:
        if isinstance(node, FunctionDef):
            if node.name == "update_pre_crawler_settings":
                self.setting_checker.in_update_pre_crawler_settings = False
            elif node.name == "update_settings":
                self.setting_checker.in_update_settings = False

    def find_call_issues(self, node: Call) -> Generator[Issue]:
        if self.looks_like_setting_method(node.func):
            yield from self.check_method_call(node)
            return

        if self.looks_like_settings_callable(node.func):
            yield from self.check_settings_callable(node)
            return

    def check_method_call(self, node: Call) -> Generator[Issue]:
        """Handle issues for calls that look like setting methods."""
        default_arg_index = 1
        assert isinstance(node.func, Attribute)
        name: Constant | None = None
        value_or_default: expr | None = None
        if node.args and isinstance(node.args[0], Constant):
            name = node.args[0]
        if len(node.args) >= (default_arg_index + 1):
            value_or_default = node.args[default_arg_index]
        else:
            for kw in node.keywords:
                if not node.args and kw.arg == "name":
                    if not isinstance(kw.value, Constant):
                        return
                    name = kw.value
                elif kw.arg in {"value", "default"}:
                    value_or_default = kw.value
        if not name:
            return
        yield from self.setting_checker.check_name(name)
        yield from self.setting_checker.check_method(name, node)
        if node.func.attr in SETTING_SETTERS:
            if isinstance(name.value, str) and value_or_default:
                yield from self.setting_checker.check_value(
                    name.value,
                    value_or_default,
                )
        elif node.func.attr == "get" and (
            value_or_default is None
            or (
                isinstance(value_or_default, Constant)
                and value_or_default.value is None
            )
        ):
            assert isinstance(node.func.value.end_lineno, int)
            assert isinstance(node.func.value.end_col_offset, int)
            pos = Pos(
                node.func.value.end_lineno,
                node.func.value.end_col_offset + 1,
            )
            yield Issue(UNNEEDED_SETTING_GET, pos)

    def check_settings_callable(self, node: Call) -> Generator[Issue]:
        """Handle issues for calls that look like settings callables."""
        if node.args:
            yield from self.setting_checker.check_dict(node.args[0])
            return
        for kw in node.keywords:
            if kw.arg in ("values", "settings"):
                yield from self.setting_checker.check_dict(kw.value)
                return

    def find_assign_issues(self, node: Assign) -> Generator[Issue]:
        for target in node.targets:
            if (
                isinstance(target, Subscript)
                and self.looks_like_settings_variable(target.value)
                and self.looks_like_setting_constant(target.slice)
            ):
                assert isinstance(target.slice, Constant)
                assert isinstance(target.slice.value, str)
                yield from self.setting_checker.check_value(
                    target.slice.value,
                    node.value,
                )

    def find_aug_assign_issues(self, node: AugAssign) -> Generator[Issue]:
        # An augmented assignment reads the setting before writing it back.
        target = node.target
        if (
            isinstance(target, Subscript)
            and self.looks_like_settings_variable(target.value)
            and self.looks_like_setting_constant(target.slice)
        ):
            assert isinstance(target.slice, Constant)
            name = target.slice.value
            assert isinstance(name, str)
            if name in SETTINGS:
                yield from self.setting_checker.check_subscript_read(
                    SETTINGS[name],
                    target,
                )

    def looks_like_setting_method(self, func: expr) -> bool:
        if not isinstance(func, Attribute):
            return False
        if not self.looks_like_settings_variable(func.value):
            return False
        return func.attr in SETTING_METHODS

    def looks_like_settings_callable(self, func: expr) -> bool:
        if not isinstance(func, (Attribute, Name)):
            return False
        if isinstance(func, Name):
            return func.id in self.NON_METHOD_SETTINGS_CALLABLES
        assert isinstance(func, Attribute)
        return func.attr in self.NON_METHOD_SETTINGS_CALLABLES or (
            func.attr in ("setdict", "update")
            and self.looks_like_settings_variable(func.value)
        )

    def find_compare_issues(self, node: Compare) -> Generator[Issue]:
        if (
            node.ops
            and isinstance(node.ops[0], (In, NotIn))
            and isinstance(node.left, Constant)
            and self.looks_like_settings_variable(node.comparators[0])
        ):
            yield from self.setting_checker.check_name(node.left)

    def find_subscript_issues(self, node: Subscript) -> Generator[Issue]:
        if not self.looks_like_settings_variable(
            node.value,
        ) or not self.looks_like_setting_constant(node.slice):
            return
        if isinstance(node.slice, Constant) and isinstance(node.slice.value, str):
            yield from self.setting_checker.check_name(node.slice)
            yield from self.setting_checker.check_subscript(node.slice.value, node)

    def looks_like_settings_variable(self, value: expr) -> bool:
        while isinstance(value, Attribute):
            if value.attr == "settings":
                return True
            value = value.value
        return isinstance(value, Name) and value.id == "settings"

    def looks_like_setting_constant(self, value: expr) -> bool:
        return isinstance(value, Constant) and isinstance(value.value, str)


class SettingModuleIssueFinder(NodeVisitor):
    def __init__(self, context: Context, file: Path, setting_checker: SettingChecker):
        super().__init__()
        self.context = context
        self.file = file.absolute()
        self.issues: list[Issue] = []
        self.setting_checker = setting_checker

    def check(self, tree: Module) -> Generator[Issue]:
        self.visit(tree)
        yield from self.issues

    def visit_Module(self, node: Module) -> None:  # pylint: disable=invalid-name
        self.check_body_level_issues(node)
        self.check_all_nodes_issues(node)

    def check_body_level_issues(self, node: Module) -> None:
        seen: dict[str, LineNumber] = {}
        for child in node.body:
            if isinstance(child, Assign):
                seen = self.check_assignment_redefinition(child, seen)
            elif isinstance(child, (ImportFrom, Import)):
                self.check_import_statement(child)

    def check_assignment_redefinition(
        self,
        node: Assign,
        seen: dict[str, LineNumber],
    ) -> dict[str, LineNumber]:
        for target in node.targets:
            if not (isinstance(target, Name) and target.id.isupper()):
                continue
            name = target.id
            pos = Pos.from_node(node)
            if name in seen:
                detail = f"seen first at line {seen[name]}"
                self.issues.append(Issue(REDEFINED_SETTING, pos, detail))
                continue
            seen[name] = pos.line
        return seen

    def check_import_statement(self, node: Import | ImportFrom) -> None:
        for import_alias in node.names:
            name = import_alias.asname or import_alias.name
            pos = Pos.from_node(node, import_column(import_alias))
            if not name.isupper():
                self.issues.extend(self.setting_checker.check_lowercase_name(name, pos))
                continue
            self.issues.append(Issue(IMPORTED_SETTING, pos))
            for issue in self.setting_checker.check_name((node, import_alias)):
                self.issues.append(issue)

    def check_all_nodes_issues(self, node: Module) -> None:
        processor = SettingsModuleSettingsProcessor(self.context, self.setting_checker)

        def visit_nested_body(child) -> None:
            visit_body(child.body)
            for attr in ("orelse", "finalbody", "handlers"):
                sub = getattr(child, attr, None)
                if sub:
                    if attr == "handlers":
                        for handler in sub:
                            visit_body(getattr(handler, "body", []))
                    else:
                        visit_body(sub)

        def visit_body(body):
            for child in body:
                if isinstance(child, (ClassDef, FunctionDef)):
                    pos = Pos.from_node(child, definition_column(child))
                    if not child.name.isupper():
                        self.issues.extend(
                            self.setting_checker.check_lowercase_name(child.name, pos)
                        )
                        continue
                    self.issues.append(Issue(IMPROPER_SETTING_DEFINITION, pos))
                    issue_generator = self.setting_checker.check_name(child)
                    self.issues.extend(issue_generator)
                elif isinstance(child, (Import, ImportFrom)):
                    processor.process_import(child)
                elif isinstance(child, Assign):
                    issue_generator = processor.process_assignment(child)
                    self.issues.extend(issue_generator)
                elif hasattr(child, "body"):
                    visit_nested_body(child)

        visit_body(node.body)
        self.issues.extend(processor.iter_issues())


class SettingsModuleSettingsProcessor:  # pylint: disable=too-many-instance-attributes
    def __init__(self, context: Context, setting_checker: SettingChecker):
        self.context = context
        self.seen_settings: set[str] = set()
        self.robotstxt_obey_values: list[tuple[bool, int, int]] = []
        self.setting_values: list[tuple[str, Any, int, int]] = []
        self.session_enabled = False
        self.session_pool_sizes: list[expr] = []
        self.setting_checker = setting_checker
        self.imports: dict[str, str] = {}
        # Setting name to the value add-ons leave it at and the package of the
        # add-on that sets it.
        self.addon_settings: dict[str, tuple[Any, str]] = {}
        self.zyte_api_params: dict[str, tuple[expr, Pos]] = {}

    def process_assignment(self, assignment: Assign) -> Generator[Issue]:
        for target in assignment.targets:
            if not isinstance(target, Name):
                continue
            if not target.id.isupper():
                yield from self.setting_checker.check_lowercase_name(
                    target.id, Pos.from_node(target)
                )
                continue
            yield from self.setting_checker.check_name(target)
            name = target.id
            self.seen_settings.add(name)
            if name == "ADDONS":
                yield from self.process_addons(assignment)
            yield from self.process_setting(name, assignment)

    def resolve_import_path(self, node) -> str:
        """Recursively resolve the import path for a Name or Attribute node, using self.imports for base names."""
        if isinstance(node, Name):
            return self.imports.get(node.id, node.id)
        assert isinstance(node, Attribute)
        base = self.resolve_import_path(node.value)
        return f"{base}.{node.attr}"

    def process_addons(self, assignment: Assign) -> Generator[Issue]:
        if not is_dict(assignment.value):
            return
        assert isinstance(assignment.value, (Call, Dict))
        entries: list[AddonEntry] = []
        for key, value in iter_dict(assignment.value):
            import_path = None
            if (
                isinstance(key, Name)
                and key.id in self.imports
                and self.imports[key.id] in ADDONS
            ):
                import_path = self.imports[key.id]
            elif isinstance(key, Constant) and isinstance(key.value, str):
                import_path = key.value
            elif isinstance(key, Attribute):
                import_path = self.resolve_import_path(key)
            if import_path not in ADDONS:
                continue
            addon = ADDONS[import_path]
            for setting, setting_value in addon.get_settings(
                self.context.project
            ).items():
                self.add_addon_setting(setting, setting_value, addon.package)
            priority, is_literal = extract_literal_value(value)
            # A non-literal priority cannot be compared, and None disables the
            # add-on.
            if is_literal and isinstance(priority, (int, float)):
                entries.append((addon, import_path, priority, value))
        yield from self.check_addon_order(entries)

    def add_addon_setting(self, name: str, value: Any, package: str) -> None:
        """Record that the add-on from *package* sets *name* to *value*.

        When add-ons disagree about the value, the resulting one is unknown:
        add-ons are probed in isolation, so what they do together, e.g. which
        entries they each add to a component priority dict, is not known.
        """
        if name in self.addon_settings:
            known_value, package = self.addon_settings[name]
            if known_value != value:
                value = UNKNOWN_SETTING_VALUE
        self.addon_settings[name] = (value, package)

    @staticmethod
    def check_addon_order(entries: list[AddonEntry]) -> Generator[Issue]:
        """Report add-ons that run before an add-on they must run after.

        Scrapy sorts add-ons by priority value with a stable sort, so add-ons
        sharing a priority value run in definition order.
        """
        ranks = {
            addon.package: (priority, index)
            for index, (addon, _, priority, _node) in enumerate(entries)
        }
        paths = {addon.package: import_path for addon, import_path, _, _node in entries}
        for index, (addon, import_path, priority, node) in enumerate(entries):
            for package in sorted(addon.after):
                if package not in ranks or (priority, index) > ranks[package]:
                    continue
                yield Issue(
                    WRONG_ADDON_ORDER,
                    Pos.from_node(node),
                    detail=f"{import_path} must run after {paths[package]}",
                )

    def process_setting(self, name: str, assignment: Assign) -> Generator[Issue]:
        if name == "ROBOTSTXT_OBEY":
            self.process_robotstxt(assignment)
        elif name in PARAM_SETTINGS:
            self.zyte_api_params[name] = (assignment.value, Pos.from_node(assignment))
        elif name in SESSION_SETTINGS:
            self.process_session(name, assignment)
        self.record_setting_value(name, assignment)
        yield from self.check_throttling(name, assignment)
        yield from self.setting_checker.check_value(name, assignment.value)

    def record_setting_value(self, name: str, assignment: Assign) -> None:
        """Record the value of *name* for a later comparison against its
        effective default, which add-ons can only be known to change once the
        entire settings module has been read."""
        if name not in SETTINGS:
            return
        setting_value, is_literal = extract_literal_value(assignment.value)
        if not is_literal:
            return
        try:
            parsed_value = SETTINGS[name].parse(setting_value)
        except (ValueError, TypeError):
            return
        self.setting_values.append(
            (name, parsed_value, assignment.value.lineno, assignment.value.col_offset),
        )

    def check_throttling(self, name: str, assignment: Assign) -> Generator[Issue]:
        if name not in {"CONCURRENT_REQUESTS_PER_DOMAIN", "DOWNLOAD_DELAY"}:
            return
        if not isinstance(assignment.value, Constant):
            return
        value = assignment.value.value
        if not isinstance(value, (int, float)):
            return
        if (name == "CONCURRENT_REQUESTS_PER_DOMAIN" and value > 1) or (
            name == "DOWNLOAD_DELAY" and value < 1.0
        ):
            pos = Pos.from_node(assignment.value)
            yield Issue(LOW_PROJECT_THROTTLING, pos)

    def process_session(self, name: str, assignment: Assign) -> None:
        if name == "ZYTE_API_SESSION_ENABLED":
            if isinstance(assignment.value, Constant):
                with suppress(ValueError):
                    self.session_enabled = getbool(assignment.value.value)
        elif name == "ZYTE_API_SESSION_POOL_SIZE":
            self.session_pool_sizes.append(assignment.value)
        elif is_dict(assignment.value):
            assert isinstance(assignment.value, (Call, Dict))
            for _, pool in iter_dict(assignment.value):
                if not is_dict(pool):
                    continue
                assert isinstance(pool, (Call, Dict))
                self.session_pool_sizes.extend(
                    value
                    for key, value in iter_dict(pool)
                    if isinstance(key, Constant) and key.value == "size"
                )

    def process_robotstxt(self, child: Assign) -> None:
        value = True
        col_offset = child.col_offset
        if isinstance(child.value, Constant):
            col_offset = child.value.col_offset
            # If the value is not a valid boolean, assume True to
            # avoid reporting the setting as being disabled, and
            # instead let a check about wrong setting values handle
            # it.
            with suppress(ValueError):
                value = getbool(child.value.value)
        self.robotstxt_obey_values.append((value, child.lineno, col_offset))

    def iter_issues(self) -> Generator[Issue]:
        yield from self.validate_user_agent()
        yield from self.validate_robotstxt()
        yield from self.validate_throttling()
        yield from self.validate_session_rotation()
        yield from self.validate_missing_changing_settings()
        yield from self.validate_redundant_values()
        yield from find_param_issues(
            self.zyte_api_params,
            {},
            provider=self.context.project.uses_scrapy_poet,
        )

    def validate_user_agent(self) -> Generator[Issue]:
        if "USER_AGENT" not in self.seen_settings:
            yield Issue(NO_PROJECT_USER_AGENT)

    def validate_robotstxt(self) -> Generator[Issue]:
        if not self.robotstxt_obey_values:
            yield Issue(ROBOTS_TXT_IGNORED_BY_DEFAULT)
        elif all(not value for value, *_ in self.robotstxt_obey_values):
            _, line, column = self.robotstxt_obey_values[0]
            yield Issue(ROBOTS_TXT_IGNORED_BY_DEFAULT, Pos(line, column))

    def validate_throttling(self) -> Generator[Issue]:
        if not all(
            setting in self.seen_settings
            for setting in (
                "CONCURRENT_REQUESTS_PER_DOMAIN",
                "DOWNLOAD_DELAY",
            )
        ):
            yield Issue(INCOMPLETE_PROJECT_THROTTLING)

    def validate_session_rotation(self) -> Generator[Issue]:
        if not self.session_enabled:
            return
        if "ZYTE_API_SESSION_POOL_SIZE" not in self.seen_settings:
            yield Issue(SESSION_ROTATION)
        for node in self.session_pool_sizes:
            if not isinstance(node, Constant) or not isinstance(node.value, (int, str)):
                continue
            try:
                size = int(node.value)
            except ValueError:
                continue
            if size != 1:
                yield Issue(SESSION_ROTATION, Pos.from_node(node))

    def validate_missing_changing_settings(self) -> Generator[Issue]:
        for name, setting in SETTINGS.items():
            if (
                name in self.seen_settings
                or name.endswith("_BASE")
                or name in self.addon_settings
            ):
                continue
            default = setting.default_value
            if isinstance(default, UnknownSettingValue):
                continue
            if not default or not default.history:
                continue
            history = default.history
            assert len(history) == MAX_DEFAULT_VALUE_HISTORY
            assert UNKNOWN_UNSUPPORTED_VERSION in history
            old_value = history[UNKNOWN_UNSUPPORTED_VERSION]
            if UNKNOWN_FUTURE_VERSION in history:
                new_value = history[UNKNOWN_FUTURE_VERSION]
                detail = (
                    f"{name} changes from {old_value!r} to {new_value!r} in a "
                    f"future version of {setting.package}"
                )
                issue = Issue(MISSING_CHANGING_SETTING, detail=detail)
                yield issue
                continue
            requirements = self.context.project.frozen_requirements
            if not requirements or setting.package not in requirements:
                continue
            project_version = requirements[setting.package]
            change_version, new_value = next(iter(history.items()))  # pylint: disable=stop-iteration-return
            assert isinstance(change_version, Version)
            if project_version >= change_version:
                continue
            detail = (
                f"{name} changes from {old_value!r} to {new_value!r} in "
                f"{setting.package} {change_version}"
            )
            issue = Issue(MISSING_CHANGING_SETTING, detail=detail)
            yield issue

    def validate_redundant_values(self) -> Generator[Issue]:
        for name, value, line, column in self.setting_values:
            default, detail = self.get_effective_default(name)
            if default is UNKNOWN_SETTING_VALUE or value != default:
                continue
            if self.is_changing_setting(name):
                continue
            yield Issue(REDUNDANT_SETTING_VALUE, Pos(line, column), detail=detail)

    def get_effective_default(self, name: str) -> tuple[Any, str | None]:
        """Return the value *name* has when the settings module does not set
        it, and a detail string when an add-on is what sets it."""
        if name in self.addon_settings:
            value, package = self.addon_settings[name]
            return value, f"already set by the {package} add-on"
        return SETTINGS[name].get_default_value(self.context.project), None

    def is_changing_setting(self, name: str) -> bool:
        setting = SETTINGS[name]
        default = setting.default_value
        if isinstance(default, UnknownSettingValue) or not default.history:
            return False
        history = default.history
        assert len(history) == MAX_DEFAULT_VALUE_HISTORY
        assert UNKNOWN_UNSUPPORTED_VERSION in history
        assert UNKNOWN_FUTURE_VERSION not in history
        requirements = self.context.project.frozen_requirements
        assert setting.package in requirements
        project_version = requirements[setting.package]
        change_version = next(
            iter(k for k in history if k != UNKNOWN_UNSUPPORTED_VERSION),
        )
        assert isinstance(change_version, Version)
        return project_version < change_version

    def process_import(self, node: Import | ImportFrom) -> None:
        if isinstance(node, Import):
            for import_alias in node.names:
                name = import_alias.asname or import_alias.name
                self.imports[name] = import_alias.name
        elif isinstance(node, ImportFrom):
            for import_alias in node.names:
                name = import_alias.asname or import_alias.name
                self.imports[name] = f"{node.module}.{import_alias.name}"
