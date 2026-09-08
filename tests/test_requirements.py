from packaging.utils import canonicalize_name
from packaging.version import Version

from scrapy_lint.data.packages import PACKAGES
from scrapy_lint.finders.requirements import RequirementsIssueFinder

from . import NO_ISSUE, Cases, ExpectedIssue, File, cases
from .helpers import check_project

SCRAPY_FUTURE_VERSION = Version("3.0.0")
SCRAPY_HIGHEST_KNOWN = PACKAGES["scrapy"].highest_known_version
SCRAPY_LOWEST_SAFE = PACKAGES["scrapy"].lowest_safe_version
SCRAPY_INSECURE_VERSION = Version("2.11.1")
SCRAPY_LOWEST_SUPPORTED = PACKAGES["scrapy"].lowest_supported_version
SCRAPY_ANCIENT_VERSION = Version("2.0.0")

CASES: Cases = (
    # No scrapy.cfg file: still works because the root directory is the working
    # directory where scrapy-lint is run.
    (
        (File("", path="requirements.txt"),),
        ExpectedIssue(
            "SCP13 incomplete requirements freeze",
            path="requirements.txt",
        ),
        {},
    ),
    # Non-standard requirements file name
    (
        (File("", path="scrapy.cfg"), File("", path="requirements-dev.txt")),
        NO_ISSUE,
        {},
    ),
    # SCP13 incomplete requirement freeze
    *(
        ((File("", path="scrapy.cfg"), File(requirements, path=path)), issues, {})
        for path in ("requirements.txt",)
        for requirements, issues in (
            *(
                (requirements, NO_ISSUE)
                for requirements in (
                    # All required dependencies with standard package names
                    "\n".join(
                        [
                            f"scrapy=={SCRAPY_HIGHEST_KNOWN}",
                            "cryptography==41.0.4",
                            "cssselect==1.2.0",
                            "lxml==4.9.3",
                            "parsel==1.8.1",
                            "protego==0.3.0",
                            "pyOpenSSL==23.2.0",
                            "queuelib==1.7.0",
                            "service-identity==23.1.0",
                            "Twisted==23.8.0",
                            "w3lib==2.1.2",
                            "zope.interface==6.0",
                        ],
                    ),
                    # Different package name formats (service_identity vs
                    # service-identity, twisted vs Twisted)
                    "\n".join(
                        [
                            f"scrapy=={SCRAPY_HIGHEST_KNOWN}",
                            "cryptography==41.0.4",
                            "cssselect==1.2.0",
                            "lxml==4.9.3",
                            "parsel==1.8.1",
                            "protego==0.3.0",
                            "pyOpenSSL==23.2.0",
                            "queuelib==1.7.0",
                            "service_identity==23.1.0",
                            "twisted==23.8.0",
                            "w3lib==2.1.2",
                            "zope.interface==6.0",
                        ],
                    ),
                    # All required dependencies plus extra packages
                    "\n".join(
                        [
                            f"scrapy=={SCRAPY_HIGHEST_KNOWN}",
                            "requests==2.31.0",
                            "cryptography==41.0.4",
                            "cssselect==1.2.0",
                            "lxml==4.9.3",
                            "parsel==1.8.1",
                            "protego==0.3.0",
                            "pyOpenSSL==23.2.0",
                            "queuelib==1.7.0",
                            "service-identity==23.1.0",
                            "Twisted==23.8.0",
                            "w3lib==2.1.2",
                            "zope.interface==6.0",
                        ],
                    ),
                )
            ),
            *(
                (
                    requirements,
                    ExpectedIssue("SCP13 incomplete requirements freeze", path=path),
                )
                for requirements in (
                    # Empty requirements file
                    "",
                    # Only comments in requirements file
                    "\n".join(["# This is a comment", "# Another comment"]),
                    # Editable install (not frozen)
                    "-e git+https://github.com/scrapy/scrapy.git#egg=scrapy",
                    # Missing most required dependencies
                    "\n".join([f"scrapy=={SCRAPY_HIGHEST_KNOWN}", "requests==2.31.0"]),
                    # Missing some required dependencies
                    "\n".join(
                        [
                            f"scrapy=={SCRAPY_HIGHEST_KNOWN}",
                            "cryptography==41.0.4",
                            "cssselect==1.2.0",
                            "lxml==4.9.3",
                            "parsel==1.8.1",
                        ],
                    ),
                )
            ),
        )
    ),
    # Tests for specific requirements
    *(
        (
            (File("", path="scrapy.cfg"), File(requirements, path=path)),
            (ExpectedIssue("SCP13 incomplete requirements freeze", path=path), *issues),
            {},
        )
        for path in ("requirements.txt",)
        for requirements, issues in (
            # SCP14 unsupported requirement
            # SCP15 insecure requirement
            *(
                (f"scrapy=={version}", issues)
                for version, issues in (
                    (SCRAPY_FUTURE_VERSION, ()),
                    (SCRAPY_HIGHEST_KNOWN, ()),
                    (SCRAPY_LOWEST_SAFE, ()),
                    (
                        SCRAPY_INSECURE_VERSION,
                        (
                            ExpectedIssue(
                                f"SCP15 insecure requirement: scrapy {SCRAPY_LOWEST_SAFE} implements security fixes",
                                path=path,
                            ),
                        ),
                    ),
                    (
                        SCRAPY_LOWEST_SUPPORTED,
                        (
                            ExpectedIssue(
                                f"SCP15 insecure requirement: scrapy {SCRAPY_LOWEST_SAFE} implements security fixes",
                                path=path,
                            ),
                        ),
                    ),
                    (
                        SCRAPY_ANCIENT_VERSION,
                        (
                            ExpectedIssue(
                                f"SCP14 unsupported requirement: scrapy-lint only supports scrapy {SCRAPY_LOWEST_SUPPORTED}+",
                                path=path,
                            ),
                            ExpectedIssue(
                                f"SCP15 insecure requirement: scrapy {SCRAPY_LOWEST_SAFE} implements security fixes",
                                path=path,
                            ),
                        ),
                    ),
                )
            ),
            # Non-frozen versions should not trigger SCP14/SCP15
            *(
                (requirements, ())
                for requirements in (
                    f"scrapy>={SCRAPY_ANCIENT_VERSION}",  # Ancient but not frozen
                    f"scrapy~={SCRAPY_INSECURE_VERSION}",  # Insecure but not frozen
                    f"scrapy!={SCRAPY_ANCIENT_VERSION}",  # Ancient but not frozen
                    "scrapy>=2.0.0,<3.0.0",  # Range specification
                )
            ),
            # Invalid versions should not trigger SCP14/SCP15
            ("scrapy==latest", ()),
            ("scrapy==1.0.0-beta.1.5", ()),
            ("scrapy==1.0.0-alpha..1", ()),
            # SCP16 unmaintained packages
            (
                "scrapy-crawlera",
                (
                    ExpectedIssue(
                        "SCP16 unmaintained requirement: replace with scrapy-zyte-smartproxy",
                        path=path,
                    ),
                ),
            ),
            (
                "scrapy-splash==1.2.3",
                (
                    ExpectedIssue(
                        "SCP16 unmaintained requirement: replace with one of: scrapy-playwright, scrapy-zyte-api",
                        path=path,
                    ),
                ),
            ),
            # Signs of SCP13, like editable installs (-e), should not prevent
            # the reporting of SCP14/SCP15/SCP16.
            (
                "\n".join(
                    [
                        "-e git+https://github.com/scrapy/parsel.git#egg=parsel",
                        f"scrapy=={SCRAPY_ANCIENT_VERSION}",
                        "scrapy-crawlera~=1.0.0",
                    ],
                ),
                (
                    ExpectedIssue(
                        f"SCP14 unsupported requirement: scrapy-lint only supports scrapy {SCRAPY_LOWEST_SUPPORTED}+",
                        line=2,
                        path=path,
                    ),
                    ExpectedIssue(
                        f"SCP15 insecure requirement: scrapy {SCRAPY_LOWEST_SAFE} implements security fixes",
                        line=2,
                        path=path,
                    ),
                    ExpectedIssue(
                        "SCP16 unmaintained requirement: replace with scrapy-zyte-smartproxy",
                        line=3,
                        path=path,
                    ),
                ),
            ),
        )
    ),
)


@cases(CASES)
def test(files, expected, options):
    check_project(files, expected, options)


def test_required_dependencies_are_canonical():
    for dep in RequirementsIssueFinder.REQUIRED_DEPENDENCIES:
        assert dep == canonicalize_name(dep)


def test_version_constants():
    assert SCRAPY_HIGHEST_KNOWN
    assert SCRAPY_LOWEST_SAFE
    assert SCRAPY_LOWEST_SUPPORTED

    assert SCRAPY_FUTURE_VERSION >= SCRAPY_HIGHEST_KNOWN
    assert SCRAPY_HIGHEST_KNOWN >= SCRAPY_LOWEST_SAFE
    assert SCRAPY_LOWEST_SAFE >= SCRAPY_INSECURE_VERSION
    assert SCRAPY_INSECURE_VERSION >= SCRAPY_LOWEST_SUPPORTED
    assert SCRAPY_LOWEST_SUPPORTED >= SCRAPY_ANCIENT_VERSION
