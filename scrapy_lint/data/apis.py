from packaging.version import Version

from scrapy_lint.apis import API
from scrapy_lint.versions import UNKNOWN_UNSUPPORTED_VERSION, Versioning

API_PARAMETERS = (
    API(
        path="scrapy.exporters.PythonItemExporter",
        name="binary",
        versioning=Versioning(
            deprecated_in=Version("1.1.0"),
            removed_in=Version("2.11.0"),
            sunset_guidance="use binary=False",
            removal_guidance="remove it, the output is no longer binary",
        ),
        deprecated_values=(True,),
    ),
)

API_METHODS = (
    API(
        path="scrapy.commands.ScrapyCommand",
        name="help",
        versioning=Versioning(
            deprecated_in=Version("2.17.0"),
            sunset_guidance="Scrapy never calls it, use long_desc() instead",
        ),
        discouraged_in=UNKNOWN_UNSUPPORTED_VERSION,
    ),
    API(
        path="scrapy.contracts.Contract",
        name="add_post_hook",
        versioning=Versioning(
            deprecated_in=Version("2.19.0"),
            sunset_guidance="define post_process() instead",
        ),
    ),
    API(
        path="scrapy.contracts.Contract",
        name="add_pre_hook",
        versioning=Versioning(
            deprecated_in=Version("2.19.0"),
            sunset_guidance="define pre_process() instead",
        ),
    ),
    API(
        path="scrapy.dupefilters.RFPDupeFilter",
        name="request_fingerprint",
        versioning=Versioning(
            deprecated_in=Version("2.19.0"),
            sunset_guidance="set the REQUEST_FINGERPRINTER_CLASS setting instead",
        ),
    ),
    API(
        path="scrapy.Spider",
        name="start_requests",
        versioning=Versioning(
            deprecated_in=Version("2.13.0"),
            removed_in=Version("2.16.0"),
            sunset_guidance="define start() instead",
        ),
    ),
    API(
        path="scrapy.spidermiddlewares.SpiderMiddleware",
        name="process_spider_output",
        versioning=Versioning(
            deprecated_in=Version("2.13.0"),
            removed_in=Version("2.16.0"),
            sunset_guidance="define it as an asynchronous generator instead",
        ),
        interface=True,
        # A synchronous method paired with an asynchronous one is a universal
        # spider middleware, which every Scrapy version supports.
        paired_with="process_spider_output_async",
    ),
    API(
        path="scrapy.spidermiddlewares.SpiderMiddleware",
        name="process_start_requests",
        versioning=Versioning(
            deprecated_in=Version("2.13.0"),
            removed_in=Version("2.16.0"),
            sunset_guidance="define process_start() instead",
        ),
        interface=True,
    ),
)
