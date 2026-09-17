from packaging.version import Version

from scrapy_lint.imports import ImportedObject
from scrapy_lint.versions import UNKNOWN_UNSUPPORTED_VERSION, Versioning

_INTERNAL = ImportedObject(
    versioning=Versioning(deprecated_in=Version("2.17.0")),
    discouraged_in=UNKNOWN_UNSUPPORTED_VERSION,
)
_SUNSET_2_16 = Versioning(
    deprecated_in=Version("2.13.0"),
    removed_in=Version("2.16.0"),
)
_REMOVED_IN_2_16 = ImportedObject(versioning=_SUNSET_2_16)

# Functions of w3lib.url that scrapy.utils.url re-exported.
_W3LIB_URL_FUNCTIONS = (
    "add_or_replace_parameter",
    "add_or_replace_parameters",
    "any_to_uri",
    "canonicalize_url",
    "file_uri_to_path",
    "is_url",
    "parse_data_uri",
    "parse_url",
    "path_to_file_uri",
    "safe_download_url",
    "safe_url_string",
    "url_query_cleaner",
    "url_query_parameter",
)

# Import paths of modules and objects that have been deprecated or removed. An
# entry for a module covers every object within it.
IMPORTS = {
    "scrapy.core.downloader.handlers.http10": _REMOVED_IN_2_16,
    "scrapy.core.downloader.tls.DEFAULT_CIPHERS": _INTERNAL,
    "scrapy.core.downloader.tls.METHOD_TLS": _INTERNAL,
    "scrapy.core.downloader.tls.METHOD_TLSv10": _INTERNAL,
    "scrapy.core.downloader.tls.METHOD_TLSv11": _INTERNAL,
    "scrapy.core.downloader.tls.METHOD_TLSv12": _INTERNAL,
    "scrapy.core.downloader.tls.openssl_methods": _INTERNAL,
    "scrapy.core.downloader.webclient": _REMOVED_IN_2_16,
    "scrapy.downloadermiddlewares.ajaxcrawl": _REMOVED_IN_2_16,
    "scrapy.spiders.init": _REMOVED_IN_2_16,
    "scrapy.utils.ssl.ffi_buf_to_string": _INTERNAL,
    "scrapy.utils.ssl.get_temp_key_info": _INTERNAL,
    "scrapy.utils.ssl.x509name_to_string": _INTERNAL,
    "scrapy.utils.test.TestSpider": _REMOVED_IN_2_16,
    "scrapy.utils.test.assert_gcs_environ": _REMOVED_IN_2_16,
    "scrapy.utils.test.get_ftp_content_and_delete": _REMOVED_IN_2_16,
    "scrapy.utils.test.get_gcs_content_and_delete": _REMOVED_IN_2_16,
    "scrapy.utils.test.mock_google_cloud_storage": _REMOVED_IN_2_16,
    "scrapy.utils.test.skip_if_no_boto": _REMOVED_IN_2_16,
    "scrapy.utils.testproc": _REMOVED_IN_2_16,
    "scrapy.utils.testsite": _REMOVED_IN_2_16,
    "scrapy.utils.url.escape_ajax": _REMOVED_IN_2_16,
    **{
        f"scrapy.utils.url.{name}": ImportedObject(
            versioning=_SUNSET_2_16,
            replacement=f"w3lib.url.{name}",
        )
        for name in _W3LIB_URL_FUNCTIONS
    },
    "scrapy.utils.versions.scrapy_components_versions": ImportedObject(
        versioning=_SUNSET_2_16,
        replacement="scrapy.utils.versions.get_versions",
    ),
}
