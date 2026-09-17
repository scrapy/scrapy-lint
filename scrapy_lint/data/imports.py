from __future__ import annotations

from packaging.version import Version

from scrapy_lint.imports import ImportedObject
from scrapy_lint.versions import UNKNOWN_UNSUPPORTED_VERSION, Versioning


def _discouraged(
    deprecated_in: str,
    sunset_guidance: str | None = None,
) -> ImportedObject:
    """Return an entry that is already worth dropping on any supported
    version, e.g. an implementation detail, or one whose replacement predates
    the deprecation."""
    return ImportedObject(
        versioning=Versioning(
            deprecated_in=Version(deprecated_in),
            sunset_guidance=sunset_guidance,
        ),
        discouraged_in=UNKNOWN_UNSUPPORTED_VERSION,
    )


_FORM_REQUEST = ImportedObject(
    versioning=Versioning(
        deprecated_in=Version("2.16.0"),
        undeprecated_in=Version("2.17.0"),
        sunset_guidance="use the form2request library instead",
    ),
)
_INTERNAL_2_15 = _discouraged("2.15.0")
_INTERNAL_2_17 = _discouraged("2.17.0")
_MAYBE_DEFERRED = _discouraged(
    "2.14.0",
    "use twisted.internet.defer.maybeDeferred instead",
)

# Import paths of modules and objects that have been deprecated or removed. An
# entry for a module covers every object within it.
IMPORTS = {
    "scrapy.FormRequest": _FORM_REQUEST,
    "scrapy.core.downloader.contextfactory.AcceptableProtocolsContextFactory": (
        _INTERNAL_2_15
    ),
    "scrapy.core.downloader.contextfactory.ScrapyClientContextFactory": _INTERNAL_2_15,
    "scrapy.core.downloader.contextfactory.load_context_factory_from_settings": (
        _INTERNAL_2_15
    ),
    "scrapy.core.downloader.handlers.http": _discouraged(
        "2.14.0",
        "import HTTP11DownloadHandler from scrapy.core.downloader.handlers.http11 "
        "instead",
    ),
    "scrapy.core.downloader.tls.DEFAULT_CIPHERS": _INTERNAL_2_17,
    "scrapy.core.downloader.tls.METHOD_TLS": _INTERNAL_2_17,
    "scrapy.core.downloader.tls.METHOD_TLSv10": _INTERNAL_2_17,
    "scrapy.core.downloader.tls.METHOD_TLSv11": _INTERNAL_2_17,
    "scrapy.core.downloader.tls.METHOD_TLSv12": _INTERNAL_2_17,
    "scrapy.core.downloader.tls.ScrapyClientTLSOptions": _INTERNAL_2_15,
    "scrapy.core.downloader.tls.openssl_methods": _INTERNAL_2_17,
    "scrapy.http.FormRequest": _FORM_REQUEST,
    "scrapy.http.request.form": _FORM_REQUEST,
    "scrapy.utils.decorators.defers": _MAYBE_DEFERRED,
    "scrapy.utils.defer.defer_fail": _discouraged(
        "2.14.0",
        "use twisted.internet.defer.fail instead",
    ),
    "scrapy.utils.defer.defer_result": _discouraged(
        "2.14.0",
        "use twisted.internet.defer.succeed or twisted.internet.defer.fail instead",
    ),
    "scrapy.utils.defer.defer_succeed": _discouraged(
        "2.14.0",
        "use twisted.internet.defer.succeed instead",
    ),
    "scrapy.utils.defer.mustbe_deferred": _MAYBE_DEFERRED,
    "scrapy.utils.misc.walk_modules": ImportedObject(
        versioning=Versioning(
            deprecated_in=Version("2.15.0"),
            sunset_guidance="use walk_modules_iter() instead",
        ),
    ),
    "scrapy.utils.ssl.ffi_buf_to_string": _INTERNAL_2_17,
    "scrapy.utils.ssl.get_temp_key_info": _INTERNAL_2_17,
    "scrapy.utils.ssl.x509name_to_string": _INTERNAL_2_17,
}
