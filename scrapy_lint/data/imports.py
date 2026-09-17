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
    "scrapy.extensions.statsmailer.StatsMailer": ImportedObject(
        versioning=Versioning(
            deprecated_in=Version("2.15.0"),
            sunset_guidance=(
                "handle the spider_closed signal to send your own notifications instead"
            ),
        ),
    ),
    "scrapy.mail.MailSender": ImportedObject(
        versioning=Versioning(
            deprecated_in=Version("2.15.0"),
            sunset_guidance=(
                "use smtplib, twisted.mail.smtp or a third-party email library instead"
            ),
        ),
    ),
    "scrapy.utils.python.MutableChain": ImportedObject(
        versioning=Versioning(deprecated_in=Version("2.16.0")),
    ),
    "scrapy.utils.ssl.ffi_buf_to_string": _INTERNAL,
    "scrapy.utils.ssl.get_temp_key_info": _INTERNAL,
    "scrapy.utils.ssl.x509name_to_string": _INTERNAL,
}
