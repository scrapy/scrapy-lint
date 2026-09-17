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
        ),
        deprecated_values=(True,),
    ),
)

API_METHODS = (
    API(
        path="scrapy.FormRequest",
        name="from_response",
        versioning=Versioning(
            deprecated_in=Version("2.16.0"),
            sunset_guidance="use form2request instead",
        ),
        discouraged_in=UNKNOWN_UNSUPPORTED_VERSION,
    ),
    API(
        path="scrapy.commands.ScrapyCommand",
        name="help",
        versioning=Versioning(
            deprecated_in=Version("2.17.0"),
            sunset_guidance="Scrapy never calls it, use long_desc() instead",
        ),
        discouraged_in=UNKNOWN_UNSUPPORTED_VERSION,
    ),
)
