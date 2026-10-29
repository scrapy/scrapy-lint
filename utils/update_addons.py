# /// script
# requires-python = ">=3.10"
# dependencies = ["packaging"]
# ///
from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from json import dumps, loads
from pathlib import Path
from urllib.request import urlopen

from packaging.version import InvalidVersion, Version

OUTPUT_PATH = Path(__file__).parents[1] / "scrapy_lint" / "data" / "addons.py"
PYPI_URL = "https://pypi.org/pypi/{package}/json"
# Oldest Python that scrapy-lint supports, and the one add-ons are probed
# on, so that old releases are not ruled out by a newer interpreter.
PYTHON = "3.10"
TIMEOUT = 30
# Marker for a value the add-on does not always set to the same thing.
UNKNOWN = "\0unknown"


@dataclass(frozen=True)
class AddonSpec:
    """An add-on to probe.

    *paths* lists the import paths the add-on class is reachable under, all of
    which are written to the data file; the first importable one is probed.
    *since* is the oldest release to probe, normally the one that added the
    add-on.
    """

    package: str
    paths: tuple[str, ...]
    since: Version


ADDONS = (
    AddonSpec(
        package="duplicate-url-discarder",
        paths=("duplicate_url_discarder.Addon",),
        since=Version("0.1.0"),
    ),
    AddonSpec(
        package="scrapy-poet",
        paths=("scrapy_poet.Addon",),
        since=Version("0.26.0"),
    ),
    AddonSpec(
        package="scrapy-zyte-api",
        paths=("scrapy_zyte_api.Addon", "scrapy_zyte_api.addon.Addon"),
        since=Version("0.17.0"),
    ),
    AddonSpec(
        package="zyte-spider-templates",
        paths=("zyte_spider_templates.Addon",),
        since=Version("0.11.0"),
    ),
)

# Runs in an environment that has only the add-on, Scrapy and their
# dependencies, and prints what the add-on sets on a project that configures
# nothing else.
#
# A setting whose value changes when another setting the add-on also changes is
# set beforehand is reported as unknown: its value depends on the project, so
# the linter cannot tell what the add-on would do. So is one that points at a
# file of the probing environment.
PROBE = r'''
import os
import sys
from json import dumps

from scrapy.settings import BaseSettings, Settings

UNKNOWN = "\0unknown"
MISSING = object()


def import_path(obj):
    qualname = getattr(obj, "__qualname__", None)
    module = getattr(obj, "__module__", None)
    if not qualname or not module:
        return None
    parts = module.split(".")
    for index in range(1, len(parts) + 1):
        candidate = ".".join(parts[:index])
        if getattr(sys.modules.get(candidate), qualname, None) is obj:
            return f"{candidate}.{qualname}"
    return f"{module}.{qualname}"


def normalize(value):
    if isinstance(value, BaseSettings):
        value = {key: value[key] for key in value}
    if isinstance(value, dict):
        return {normalize(key): normalize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [normalize(item) for item in value]
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    return import_path(value)


def snapshot(settings):
    """Return the value and priority of every setting.

    The priority tells apart a setting an add-on sets to the value Scrapy
    already defaults to from one it leaves alone, which a comparison of values
    cannot.
    """
    return {
        name: (normalize(settings[name]), settings.getpriority(name))
        for name in settings
    }


def changes(addon, presets):
    """Return what *addon* sets on a project that sets only *presets*."""
    settings = Settings()
    before = snapshot(settings)
    for name, value in presets.items():
        settings.set(name, value, "project")
    addon().update_settings(settings)
    after = snapshot(settings)
    return {
        name: value
        for name, (value, priority) in after.items()
        if name not in presets and before.get(name, MISSING) != (value, priority)
    }


def environment_specific(value):
    """Return whether *value* points at a file of the probing environment.

    Such a value, e.g. a rule file that ships with a package, is different in
    every project, so what the add-on sets it to cannot be recorded.
    """
    if isinstance(value, dict):
        value = [*value, *value.values()]
    if isinstance(value, list):
        return any(environment_specific(item) for item in value)
    return isinstance(value, str) and os.path.isabs(value) and os.path.exists(value)


def load(paths):
    errors = []
    for path in paths:
        module_path, _, name = path.rpartition(".")
        try:
            module = __import__(module_path, fromlist=[name])
            return getattr(module, name)
        except (ImportError, AttributeError) as error:
            errors.append(f"{path}: {error!r}")
    raise SystemExit("; ".join(errors))


def main(paths):
    addon = load(paths)
    baseline = changes(addon, {})
    unknown = {
        name for name, value in baseline.items() if environment_specific(value)
    }
    for name, value in baseline.items():
        perturbed = changes(addon, {name: value})
        unknown.update(
            other
            for other, other_value in baseline.items()
            if other != name and perturbed.get(other, MISSING) != other_value
        )
    print(dumps({k: UNKNOWN if k in unknown else v for k, v in baseline.items()}))


main(sys.argv[1:])
'''


def main() -> None:
    """Vendor what every known add-on does to settings, release by release."""
    scrapy = release_dates("scrapy")
    addons = {spec: history(spec, scrapy) for spec in ADDONS}
    OUTPUT_PATH.write_text(render(addons), encoding="utf-8")
    print(f"Updated {OUTPUT_PATH.relative_to(Path.cwd())}")


def history(spec: AddonSpec, scrapy: dict[Version, str]) -> dict[Version, dict]:
    """Return what *spec* changes in each of its releases that changes it."""
    result: dict[Version, dict] = {}
    previous = None
    dates = release_dates(spec.package)
    for version in sorted(v for v in dates if v >= spec.since):
        changes = probe(spec, version, contemporary(scrapy, dates[version]))
        if changes is None or changes == previous:
            continue
        result[version] = changes
        previous = changes
    if not result:
        raise SystemExit(f"no release of {spec.package} could be probed")
    return result


def release_dates(package: str) -> dict[Version, str]:
    """Return when every final, non-yanked release of *package* was uploaded."""
    data = loads(download(PYPI_URL.format(package=package)))
    result = {}
    for release, files in data["releases"].items():
        try:
            version = Version(release)
        except InvalidVersion:
            continue
        published = [file for file in files if not file["yanked"]]
        if version.is_prerelease or not published:
            continue
        result[version] = min(file["upload_time_iso_8601"] for file in published)
    return result


def contemporary(scrapy: dict[Version, str], date: str) -> Version:
    """Return the newest Scrapy released no later than *date*.

    Add-ons declare no upper bound on the Scrapy versions they support, so an
    old release paired with the newest Scrapy usually fails to even import.
    """
    return max(version for version, released in scrapy.items() if released <= date)


def probe(spec: AddonSpec, version: Version, scrapy: Version) -> dict | None:
    """Return what *spec* changes at *version*, or None if it cannot be run."""
    command = (
        "uv",
        "run",
        "--no-project",
        "--quiet",
        "--python",
        PYTHON,
        "--with",
        f"{spec.package}=={version}",
        "--with",
        f"scrapy=={scrapy}",
        "python",
        "-c",
        PROBE,
        *spec.paths,
    )
    try:
        result = subprocess.run(  # noqa: S603
            command, capture_output=True, text=True, check=False, timeout=TIMEOUT * 20
        )
    except subprocess.TimeoutExpired:
        skip(spec, version, "timed out")
        return None
    if result.returncode:
        lines = result.stderr.strip().splitlines()
        skip(spec, version, lines[-1] if lines else "failed")
        return None
    return loads(result.stdout)


def skip(spec: AddonSpec, version: Version, reason: str) -> None:
    print(f"Skipped {spec.package} {version}: {reason}", file=sys.stderr)


def download(url: str) -> str:
    with urlopen(url, timeout=TIMEOUT) as response:  # noqa: S310
        return response.read().decode("utf-8")


def render(addons: dict[AddonSpec, dict[Version, dict]]) -> str:
    variables = "\n\n".join(
        f"{variable(spec)} = Addon(\n"
        f'    package="{spec.package}",\n'
        f"    settings=VersionedSettings(\n"
        f"        history={{\n{render_history(versions)}"
        f"        }},\n"
        f"    ),\n"
        f")\n"
        for spec, versions in addons.items()
    )
    entries = "".join(
        f'    "{path}": {variable(spec)},\n' for spec in addons for path in spec.paths
    )
    return (
        "# Generated by utils/update_addons.py.\n"
        "from packaging.version import Version\n\n"
        "from scrapy_lint.addons import Addon, VersionedSettings\n"
        "from scrapy_lint.settings import UNKNOWN_SETTING_VALUE\n"
        "from scrapy_lint.versions import UNKNOWN_UNSUPPORTED_VERSION\n\n"
        f"{variables}\n\n"
        f"ADDONS = {{\n{entries}}}\n"
    )


def variable(spec: AddonSpec) -> str:
    return f"{spec.package.upper().replace('-', '_')}_ADDON"


def render_history(versions: dict[Version, dict]) -> str:
    """Render the history of an add-on, oldest release first.

    The oldest release probed stands in for every older release, so that
    projects pinning one still get the oldest data available.
    """
    keys = sorted(versions)
    result = ""
    for index, version in enumerate(keys):
        key = "UNKNOWN_UNSUPPORTED_VERSION" if not index else f'Version("{version}")'
        result += f"            {key}: {{\n{render_changes(versions[version])}"
        result += "            },\n"
    return result


def render_changes(changes: dict) -> str:
    return "".join(
        f"                {dumps(name)}: {render_value(value, 4)},\n"
        for name, value in sorted(changes.items())
    )


def render_value(value, depth: int) -> str:
    """Render *value* as Python source, indented for a *depth*-level nesting."""
    if isinstance(value, str):
        return "UNKNOWN_SETTING_VALUE" if value == UNKNOWN else dumps(value)
    if isinstance(value, dict) and value:
        indent = "    " * (depth + 1)
        items = "".join(
            f"{indent}{render_value(key, depth + 1)}: {render_value(item, depth + 1)},\n"
            for key, item in value.items()
        )
        return "{\n" + items + "    " * depth + "}"
    if isinstance(value, list) and value:
        indent = "    " * (depth + 1)
        items = "".join(f"{indent}{render_value(item, depth + 1)},\n" for item in value)
        return "[\n" + items + "    " * depth + "]"
    return repr(value)


if __name__ == "__main__":
    main()
