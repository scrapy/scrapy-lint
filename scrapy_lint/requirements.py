from collections.abc import Generator, Iterable
from typing import cast

from packaging.requirements import InvalidRequirement, Requirement
from packaging.specifiers import Specifier
from packaging.utils import canonicalize_name
from packaging.version import InvalidVersion, Version

from scrapy_lint.versions import VersionRange


def iter_requirement_lines(
    lines: Iterable[str],
) -> Generator[tuple[int, str, Requirement]]:
    for line_number, line in enumerate(lines, start=1):
        clean_line = line.strip()
        if not clean_line or clean_line.startswith("#"):
            continue
        if "#" in clean_line:
            clean_line = clean_line.split("#", 1)[0].strip()
        try:
            requirement = Requirement(clean_line)
        except InvalidRequirement:
            continue
        canonical_name = cast("str", canonicalize_name(requirement.name))
        yield line_number, canonical_name, requirement


def _bumped(release: tuple[int, ...]) -> Version:
    return Version(".".join(str(part) for part in (*release[:-1], release[-1] + 1)))


def _specifier_bounds(
    specifier: Specifier,
) -> tuple[Version | None, Version | None, bool]:
    """Return the lowest version, the highest version and whether the highest
    version itself is allowed by *specifier*."""
    operator = specifier.operator
    if operator in {"==", "==="} and specifier.version.endswith(".*"):
        lowest = Version(specifier.version[:-2])
        return lowest, _bumped(lowest.release), False
    try:
        version = Version(specifier.version)
    except InvalidVersion:
        return None, None, True
    if operator in {"==", "==="}:
        return version, version, True
    if operator == "~=":
        return version, _bumped(version.release[:-1]), False
    if operator in {">=", ">"}:
        return version, None, True
    highest = version if operator in {"<=", "<"} else None
    return None, highest, operator == "<="


def version_range(requirements: Iterable[Requirement]) -> VersionRange:
    """Return the range of versions that *requirements*, all for the same
    package, allow.

    Requirements that only apply under an environment marker are ignored, as
    they do not constrain every installation of the project.
    """
    lowest: Version | None = None
    highest: Version | None = None
    highest_inclusive = True
    for requirement in requirements:
        if requirement.marker is not None:
            continue
        for specifier in requirement.specifier:
            spec_lowest, spec_highest, spec_inclusive = _specifier_bounds(specifier)
            if spec_lowest is not None and (lowest is None or spec_lowest > lowest):
                lowest = spec_lowest
            if spec_highest is not None and (
                highest is None
                or spec_highest < highest
                or (spec_highest == highest and not spec_inclusive)
            ):
                highest = spec_highest
                highest_inclusive = spec_inclusive
    return VersionRange(lowest, highest, highest_inclusive)
