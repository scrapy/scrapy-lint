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
    "http_auth_domain": Versioning(
        deprecated_in=Version("2.17.0"),
        sunset_guidance=(
            "use the HTTPAUTH_DOMAIN setting or the http_auth_domain request "
            "metadata key instead"
        ),
    ),
    "http_pass": Versioning(
        deprecated_in=Version("2.17.0"),
        sunset_guidance=(
            "use the HTTPAUTH_PASS setting or the http_pass request metadata "
            "key instead"
        ),
    ),
    "http_user": Versioning(
        deprecated_in=Version("2.17.0"),
        sunset_guidance=(
            "use the HTTPAUTH_USER setting or the http_user request metadata "
            "key instead"
        ),
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
