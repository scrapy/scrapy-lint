from packaging.version import Version

from scrapy_lint.settings import Versioning

_SPIDER_ARGUMENT = Versioning(
    deprecated_in=Version("2.14.0"),
    sunset_guidance=(
        "keep the crawler from from_crawler() and use its spider attribute instead"
    ),
)

# Deprecated parameters, keyed by the name of the method they belong to. The
# methods are those that Scrapy calls on user-defined components.
DEPRECATED_ARGUMENTS: dict[str, dict[str, Versioning]] = {
    method: {"spider": _SPIDER_ARGUMENT}
    for method in (
        "close_spider",
        "fetch",
        "open_spider",
        "process_exception",
        "process_item",
        "process_request",
        "process_response",
        "process_spider_exception",
        "process_spider_input",
        "process_spider_output",
    )
}
