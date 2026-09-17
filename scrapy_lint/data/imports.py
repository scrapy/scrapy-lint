from packaging.version import Version

from scrapy_lint.imports import ImportedObject
from scrapy_lint.versions import UNKNOWN_UNSUPPORTED_VERSION, Versioning

_INTERNAL = ImportedObject(
    versioning=Versioning(deprecated_in=Version("2.17.0")),
    discouraged_in=UNKNOWN_UNSUPPORTED_VERSION,
)

# Import paths of modules and objects that have been deprecated or removed. An
# entry for a module covers every object within it.
IMPORTS = {
    "scrapy.core.downloader.tls.DEFAULT_CIPHERS": _INTERNAL,
    "scrapy.core.downloader.tls.METHOD_TLS": _INTERNAL,
    "scrapy.core.downloader.tls.METHOD_TLSv10": _INTERNAL,
    "scrapy.core.downloader.tls.METHOD_TLSv11": _INTERNAL,
    "scrapy.core.downloader.tls.METHOD_TLSv12": _INTERNAL,
    "scrapy.core.downloader.tls.openssl_methods": _INTERNAL,
    "scrapy.extensions.feedexport.IFeedStorage": ImportedObject(
        versioning=Versioning(
            deprecated_in=Version("2.18.0"),
            sunset_guidance=(
                "follow scrapy.extensions.feedexport.FeedStorageProtocol instead"
            ),
        ),
    ),
    "scrapy.interfaces": ImportedObject(
        versioning=Versioning(
            deprecated_in=Version("2.18.0"),
            sunset_guidance="follow scrapy.spiderloader.SpiderLoaderProtocol instead",
        ),
    ),
    "scrapy.pipelines.files.FileException": ImportedObject(
        versioning=Versioning(
            deprecated_in=Version("2.18.0"),
            sunset_guidance="import it from scrapy.pipelines.media instead",
        ),
    ),
    "scrapy.utils.datatypes.CaselessDict": ImportedObject(
        versioning=Versioning(
            deprecated_in=Version("2.10.0"),
            removed_in=Version("2.18.0"),
            sunset_guidance="use CaseInsensitiveDict instead",
        ),
    ),
    "scrapy.utils.iterators.xmliter": ImportedObject(
        versioning=Versioning(
            deprecated_in=Version("2.11.1"),
            removed_in=Version("2.18.0"),
            sunset_guidance="use xmliter_lxml instead",
        ),
    ),
    "scrapy.utils.misc.md5sum": ImportedObject(
        versioning=Versioning(
            deprecated_in=Version("2.12.0"),
            removed_in=Version("2.18.0"),
        ),
    ),
    "scrapy.utils.python.re_rsearch": ImportedObject(
        versioning=Versioning(deprecated_in=Version("2.18.0")),
    ),
    "scrapy.utils.ssl.ffi_buf_to_string": _INTERNAL,
    "scrapy.utils.ssl.get_temp_key_info": _INTERNAL,
    "scrapy.utils.ssl.x509name_to_string": _INTERNAL,
}
