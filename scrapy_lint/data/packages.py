from packaging.version import Version

from scrapy_lint.packages import Package, VersionConflict

PACKAGES = {
    "scrapy": Package(
        highest_known_version=Version("2.13.2"),
        lowest_safe_version=Version("2.11.2"),
        lowest_supported_version=Version("2.0.1"),
    ),
    "scrapy-crawlera": Package(
        replacements=("scrapy-zyte-smartproxy",),
    ),
    "scrapy-splash": Package(
        replacements=("scrapy-playwright", "scrapy-zyte-api"),
    ),
}

VERSION_CONFLICTS = (
    # Lower versions use the binary export mode of PythonItemExporter, removed
    # in Scrapy 2.11.0, and fail with "TypeError: Unexpected options: binary".
    VersionConflict(
        package="scrapy",
        since=Version("2.11.0"),
        dependency="scrapinghub-entrypoint-scrapy",
        lowest_compatible=Version("0.14.1"),
    ),
)
