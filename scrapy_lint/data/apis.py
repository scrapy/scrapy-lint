from packaging.version import Version

from scrapy_lint.apis import API
from scrapy_lint.versions import UNKNOWN_UNSUPPORTED_VERSION, Versioning

INTERNAL_USE_ONLY = "intended for internal use only"

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
        droppable=True,
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
)

API_MEMBERS = (
    *(
        API(
            path="scrapy.core.downloader.tls",
            name=name,
            versioning=Versioning(
                deprecated_in=Version("2.17.0"),
                sunset_guidance=INTERNAL_USE_ONLY,
            ),
            discouraged_in=UNKNOWN_UNSUPPORTED_VERSION,
        )
        for name in (
            "DEFAULT_CIPHERS",
            "METHOD_TLS",
            "METHOD_TLSv10",
            "METHOD_TLSv11",
            "METHOD_TLSv12",
            "openssl_methods",
        )
    ),
    *(
        API(
            path="scrapy.utils.ssl",
            name=name,
            versioning=Versioning(
                deprecated_in=Version("2.17.0"),
                sunset_guidance=INTERNAL_USE_ONLY,
            ),
            discouraged_in=UNKNOWN_UNSUPPORTED_VERSION,
        )
        for name in (
            "ffi_buf_to_string",
            "get_temp_key_info",
            "x509name_to_string",
        )
    ),
)
