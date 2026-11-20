from packaging.version import Version

from scrapy_lint.packages import Package, VersionConflict

PACKAGES = {
    "scrapy": Package(
        lowest_safe_version=Version("2.17.0"),
        lowest_supported_version=Version("2.0.1"),
    ),
    "scrapy-crawlera": Package(
        replacements=("scrapy-zyte-smartproxy",),
    ),
    "scrapy-splash": Package(
        replacements=("scrapy-playwright", "scrapy-zyte-api"),
    ),
    "scrapy-zyte-api": Package(
        lowest_supported_version=Version("0.5.1"),
    ),
    "scrapy-zyte-smartproxy": Package(
        lowest_supported_version=Version("2.0.0"),
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
    # Lower versions crash building request headers before the crawl starts.
    VersionConflict(
        package="scrapy",
        since=Version("2.18.0"),
        dependency="scrapy-zyte-api",
        lowest_compatible=Version("0.36.0"),
    ),
    # download_request() became a plain coroutine method; lower versions still
    # implement it as returning a Deferred, which Scrapy no longer awaits.
    VersionConflict(
        package="scrapy",
        since=Version("2.14.0"),
        dependency="scrapy-zyte-api",
        lowest_compatible=Version("0.32.0"),
    ),
    # Lower versions call process_item() without the spider argument.
    VersionConflict(
        package="scrapy",
        since=Version("2.14.0"),
        dependency="spidermon",
        lowest_compatible=Version("1.25.1"),
    ),
    # Lower versions are incompatible; see PRs #356 and #359 upstream.
    VersionConflict(
        package="scrapy",
        since=Version("2.14.0"),
        dependency="scrapy-playwright",
        lowest_compatible=Version("0.0.45"),
    ),
    # Lower versions raise ModuleNotFoundError for scrapy.webservice at
    # startup.
    VersionConflict(
        package="scrapy",
        since=Version("2.15.0"),
        dependency="scrapyrt",
        lowest_compatible=Version("0.18.1"),
    ),
    # Lower versions are incompatible with the crawler object Scrapy passes.
    VersionConflict(
        package="scrapy",
        since=Version("2.11.0"),
        dependency="scrapyrt",
        lowest_compatible=Version("0.15.0"),
    ),
    # Lower versions pass a spider argument to engine.crawl(), removed in
    # Scrapy 2.10.0.
    VersionConflict(
        package="scrapy",
        since=Version("2.10.0"),
        dependency="scrapyrt",
        lowest_compatible=Version("0.14.0"),
    ),
    # Lower versions rely on the Proxy-Authorization header surviving to the
    # proxy, which Scrapy 2.6.2 stops forwarding on cross-origin redirects.
    VersionConflict(
        package="scrapy",
        since=Version("2.6.2"),
        dependency="scrapy-zyte-smartproxy",
        lowest_compatible=Version("2.2.0"),
    ),
)
