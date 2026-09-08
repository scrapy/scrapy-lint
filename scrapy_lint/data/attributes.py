from packaging.version import Version

from scrapy_lint.settings import Versioning

# Spider attributes with a sunset date. They all come from Scrapy itself.
SPIDER_ATTRIBUTES: dict[str, Versioning] = {
    "download_maxsize": Versioning(
        deprecated_in=Version("2.14.0"),
        sunset_guidance="use the DOWNLOAD_MAXSIZE setting instead",
    ),
    "download_timeout": Versioning(
        deprecated_in=Version("2.14.0"),
        sunset_guidance="use the DOWNLOAD_TIMEOUT setting instead",
    ),
    "download_warnsize": Versioning(
        deprecated_in=Version("2.14.0"),
        sunset_guidance="use the DOWNLOAD_WARNSIZE setting instead",
    ),
    "max_concurrent_requests": Versioning(
        deprecated_in=Version("2.14.0"),
        sunset_guidance="use the CONCURRENT_REQUESTS_PER_DOMAIN setting instead",
    ),
    "user_agent": Versioning(
        deprecated_in=Version("2.14.0"),
        sunset_guidance="use the USER_AGENT setting instead",
    ),
}
