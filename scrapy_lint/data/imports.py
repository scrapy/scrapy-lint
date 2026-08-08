from packaging.version import Version

from scrapy_lint.imports import ImportedObject
from scrapy_lint.versions import Versioning

# Import paths of modules and objects that have been deprecated or removed. An
# entry for a module covers every object within it.
IMPORTS = {
    "scrapy.core.downloader.tls.DEFAULT_CIPHERS": ImportedObject(
        versioning=Versioning(deprecated_in=Version("2.17.0")),
    ),
    "scrapy.core.downloader.tls.METHOD_TLS": ImportedObject(
        versioning=Versioning(deprecated_in=Version("2.17.0")),
    ),
    "scrapy.core.downloader.tls.METHOD_TLSv10": ImportedObject(
        versioning=Versioning(deprecated_in=Version("2.17.0")),
    ),
    "scrapy.core.downloader.tls.METHOD_TLSv11": ImportedObject(
        versioning=Versioning(deprecated_in=Version("2.17.0")),
    ),
    "scrapy.core.downloader.tls.METHOD_TLSv12": ImportedObject(
        versioning=Versioning(deprecated_in=Version("2.17.0")),
    ),
    "scrapy.core.downloader.tls.openssl_methods": ImportedObject(
        versioning=Versioning(deprecated_in=Version("2.17.0")),
    ),
    "scrapy.utils.ssl.ffi_buf_to_string": ImportedObject(
        versioning=Versioning(deprecated_in=Version("2.17.0")),
    ),
    "scrapy.utils.ssl.get_temp_key_info": ImportedObject(
        versioning=Versioning(deprecated_in=Version("2.17.0")),
    ),
    "scrapy.utils.ssl.x509name_to_string": ImportedObject(
        versioning=Versioning(deprecated_in=Version("2.17.0")),
    ),
}
