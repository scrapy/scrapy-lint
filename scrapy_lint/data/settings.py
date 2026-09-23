from __future__ import annotations

from packaging.version import Version

from scrapy_lint.settings import (
    UNKNOWN_SETTING_VALUE,
    Setting,
    SettingType,
    VersionedValue,
)
from scrapy_lint.versions import (
    UNKNOWN_FUTURE_VERSION,
    UNKNOWN_UNSUPPORTED_VERSION,
    Versioning,
)

PREDEFINED_SUGGESTIONS = {
    # NOTE: Somewhat arbitrary for the sake of having a few suggestions to
    # check in tests:
    #
    # - 1 with 1 suggestion
    # - 1 with 2+ suggestions
    # - 1 with a non-Scrapy suggestion
    #
    # Going forward, as we add new suggestions based on actual wrong setting
    # names seen in the wild (due to human or AI error), we can remove these
    # as the scenarios above get covered by real suggestions.
    "CONCURRENCY": ["CONCURRENT_REQUESTS", "CONCURRENT_REQUESTS_PER_DOMAIN"],
    "DELAY": ["DOWNLOAD_DELAY"],
    "TIMEOUT": ["DOWNLOAD_TIMEOUT", "TIMEOUT_LIMIT"],
}
MAX_AUTOMATIC_SUGGESTIONS = 3
MIN_AUTOMATIC_SUGGESTION_SCORE = 0.7

FEEDS_KEY_VERSION_ADDED = {
    "batch_item_count": Version("2.3.0"),
    "item_classes": Version("2.6.0"),
    "item_filter": Version("2.6.0"),
    "item_export_kwargs": Version("2.4.0"),
    "overwrite": Version("2.4.0"),
    "postprocessing": Version("2.6.0"),
}

SETTINGS = {
    # Active (i.e. neither deprecated nor removed) Scrapy built-in settings, in
    # order of appearance in
    # https://github.com/scrapy/scrapy/blob/master/scrapy/settings/default_settings.py
    "ADDONS": Setting(
        type=SettingType.COMP_PRIO_DICT,
        default_value=VersionedValue({}),
        is_pre_crawler=True,
        versioning=Versioning(added_in=Version("2.10.0")),
    ),
    "ASYNCIO_EVENT_LOOP": Setting(
        type=SettingType.OPT_OBJ,
        default_value=VersionedValue(None),
        is_pre_crawler=True,
        versioning=Versioning(added_in=Version("2.4.0")),
    ),
    "AUTOTHROTTLE_DEBUG": Setting(
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
    ),
    "AUTOTHROTTLE_ENABLED": Setting(
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
    ),
    "AUTOTHROTTLE_MAX_DELAY": Setting(
        type=SettingType.FLOAT,
        default_value=VersionedValue(60.0),
    ),
    "AUTOTHROTTLE_START_DELAY": Setting(
        type=SettingType.FLOAT,
        default_value=VersionedValue(5.0),
    ),
    "AUTOTHROTTLE_TARGET_CONCURRENCY": Setting(
        type=SettingType.FLOAT,
        default_value=VersionedValue(1.0),
    ),
    "AWS_MAX_POOL_CONNECTIONS": Setting(
        type=SettingType.OPT_INT,
        default_value=VersionedValue(None),
        versioning=Versioning(added_in=Version("2.18.0")),
    ),
    "BOT_NAME": Setting(
        type=SettingType.STR,
        default_value=VersionedValue("scrapybot"),
    ),
    "CLOSESPIDER_ERRORCOUNT": Setting(
        type=SettingType.INT,
        default_value=VersionedValue(0),
    ),
    "CLOSESPIDER_ITEMCOUNT": Setting(
        type=SettingType.INT,
        default_value=VersionedValue(0),
    ),
    "CLOSESPIDER_PAGECOUNT": Setting(
        type=SettingType.INT,
        default_value=VersionedValue(0),
    ),
    "CLOSESPIDER_TIMEOUT": Setting(
        type=SettingType.FLOAT,
        default_value=VersionedValue(0),
    ),
    "COMMANDS_MODULE": Setting(
        type=SettingType.STR,
        default_value=VersionedValue(""),
        is_pre_crawler=True,
    ),
    "COMPRESSION_ENABLED": Setting(
        type=SettingType.BOOL,
        default_value=VersionedValue(True),
    ),
    "CONCURRENT_ITEMS": Setting(
        type=SettingType.INT,
        default_value=VersionedValue(100),
    ),
    "CONCURRENT_REQUESTS": Setting(
        type=SettingType.INT,
        default_value=VersionedValue(16),
    ),
    "CONCURRENT_REQUESTS_PER_DOMAIN": Setting(
        type=SettingType.INT,
        default_value=VersionedValue(8),
    ),
    "COOKIES_DEBUG": Setting(
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
    ),
    "COOKIES_ENABLED": Setting(
        type=SettingType.BOOL,
        default_value=VersionedValue(True),
    ),
    "DEFAULT_DROPITEM_LOG_LEVEL": Setting(
        type=SettingType.LOG_LEVEL,
        default_value=VersionedValue("WARNING"),
        versioning=Versioning(added_in=Version("2.13.0")),
    ),
    "DEFAULT_ITEM_CLASS": Setting(
        type=SettingType.OBJ,
        default_value=VersionedValue("scrapy.item.Item"),
    ),
    "DEFAULT_REQUEST_HEADERS": Setting(
        type=SettingType.DICT,
        default_value=VersionedValue(
            {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en",
            },
        ),
    ),
    "DEPTH_LIMIT": Setting(type=SettingType.INT, default_value=VersionedValue(0)),
    "DEPTH_PRIORITY": Setting(type=SettingType.INT, default_value=VersionedValue(0)),
    "DEPTH_STATS_VERBOSE": Setting(
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
    ),
    "DNSCACHE_ENABLED": Setting(
        type=SettingType.BOOL,
        default_value=VersionedValue(True),
        is_pre_crawler=True,
    ),
    "DNSCACHE_SIZE": Setting(
        type=SettingType.INT,
        default_value=VersionedValue(10000),
        is_pre_crawler=True,
    ),
    "DNS_TIMEOUT": Setting(
        type=SettingType.FLOAT,
        default_value=VersionedValue(60),
        is_pre_crawler=True,
    ),
    "DOWNLOAD_BIND_ADDRESS": Setting(
        type=SettingType.BIND_ADDRESS,
        default_value=VersionedValue(None),
        versioning=Versioning(added_in=Version("2.15.0")),
    ),
    "DOWNLOAD_DELAY": Setting(type=SettingType.FLOAT, default_value=VersionedValue(0)),
    "DOWNLOAD_DELAY_JITTER": Setting(
        type=SettingType.FLOAT,
        default_value=VersionedValue(0.5),
        versioning=Versioning(added_in=Version("2.19.0")),
    ),
    "DOWNLOAD_FAIL_ON_DATALOSS": Setting(
        type=SettingType.BOOL,
        default_value=VersionedValue(True),
    ),
    "DOWNLOAD_HANDLERS": Setting(
        type=SettingType.BASED_OBJ_DICT,
        default_value=VersionedValue({}),
    ),
    "DOWNLOAD_HANDLERS_BASE": Setting(
        default_value=VersionedValue(
            {
                "data": "scrapy.core.downloader.handlers.datauri.DataURIDownloadHandler",
                "file": "scrapy.core.downloader.handlers.file.FileDownloadHandler",
                "http": "scrapy.core.downloader.handlers.http.HTTPDownloadHandler",
                "https": "scrapy.core.downloader.handlers.http.HTTPDownloadHandler",
                "s3": "scrapy.core.downloader.handlers.s3.S3DownloadHandler",
                "ftp": "scrapy.core.downloader.handlers.ftp.FTPDownloadHandler",
            },
        ),
    ),
    "DOWNLOAD_MAXSIZE": Setting(
        type=SettingType.INT,
        default_value=VersionedValue(1024 * 1024 * 1024),
    ),
    "DOWNLOAD_TIMEOUT": Setting(
        type=SettingType.FLOAT,
        default_value=VersionedValue(180),
    ),
    "DOWNLOAD_TLS_MAX_VERSION": Setting(
        type=SettingType.ENUM_STR,
        values=(None, "TLSv1.0", "TLSv1.1", "TLSv1.2", "TLSv1.3"),
        default_value=VersionedValue(None),
        versioning=Versioning(added_in=Version("2.17.0")),
    ),
    "DOWNLOAD_TLS_MIN_VERSION": Setting(
        type=SettingType.ENUM_STR,
        values=(None, "TLSv1.0", "TLSv1.1", "TLSv1.2", "TLSv1.3"),
        default_value=VersionedValue(None),
        versioning=Versioning(added_in=Version("2.17.0")),
    ),
    "DOWNLOAD_WARNSIZE": Setting(
        type=SettingType.INT,
        default_value=VersionedValue(32 * 1024 * 1024),
    ),
    "DOWNLOAD_VERIFY_CERTIFICATES": Setting(
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
        versioning=Versioning(added_in=Version("2.15.0")),
    ),
    "DOWNLOADER": Setting(
        type=SettingType.OBJ,
        default_value=VersionedValue("scrapy.core.downloader.Downloader"),
    ),
    "DOWNLOADER_CLIENT_TLS_CIPHERS": Setting(
        type=SettingType.STR,
        default_value=VersionedValue("DEFAULT"),
        versioning=Versioning(nullable_since=Version("2.17.0")),
    ),
    "DOWNLOADER_CLIENT_TLS_VERBOSE_LOGGING": Setting(
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
    ),
    "DOWNLOADER_MIDDLEWARES": Setting(
        type=SettingType.BASED_COMP_PRIO_DICT,
        default_value=VersionedValue({}),
    ),
    "DOWNLOADER_MIDDLEWARES_BASE": Setting(
        default_value=VersionedValue(
            history={
                Version("2.11.2"): {
                    "scrapy.downloadermiddlewares.offsite.OffsiteMiddleware": 50,  # added
                    "scrapy.downloadermiddlewares.robotstxt.RobotsTxtMiddleware": 100,
                    "scrapy.downloadermiddlewares.httpauth.HttpAuthMiddleware": 300,
                    "scrapy.downloadermiddlewares.downloadtimeout.DownloadTimeoutMiddleware": 350,
                    "scrapy.downloadermiddlewares.defaultheaders.DefaultHeadersMiddleware": 400,
                    "scrapy.downloadermiddlewares.useragent.UserAgentMiddleware": 500,
                    "scrapy.downloadermiddlewares.retry.RetryMiddleware": 550,
                    "scrapy.downloadermiddlewares.ajaxcrawl.AjaxCrawlMiddleware": 560,
                    "scrapy.downloadermiddlewares.redirect.MetaRefreshMiddleware": 580,
                    "scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware": 590,
                    "scrapy.downloadermiddlewares.redirect.RedirectMiddleware": 600,
                    "scrapy.downloadermiddlewares.cookies.CookiesMiddleware": 700,
                    "scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware": 750,
                    "scrapy.downloadermiddlewares.stats.DownloaderStats": 850,
                    "scrapy.downloadermiddlewares.httpcache.HttpCacheMiddleware": 900,
                },
                UNKNOWN_UNSUPPORTED_VERSION: {
                    "scrapy.downloadermiddlewares.robotstxt.RobotsTxtMiddleware": 100,
                    "scrapy.downloadermiddlewares.httpauth.HttpAuthMiddleware": 300,
                    "scrapy.downloadermiddlewares.downloadtimeout.DownloadTimeoutMiddleware": 350,
                    "scrapy.downloadermiddlewares.defaultheaders.DefaultHeadersMiddleware": 400,
                    "scrapy.downloadermiddlewares.useragent.UserAgentMiddleware": 500,
                    "scrapy.downloadermiddlewares.retry.RetryMiddleware": 550,
                    "scrapy.downloadermiddlewares.ajaxcrawl.AjaxCrawlMiddleware": 560,
                    "scrapy.downloadermiddlewares.redirect.MetaRefreshMiddleware": 580,
                    "scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware": 590,
                    "scrapy.downloadermiddlewares.redirect.RedirectMiddleware": 600,
                    "scrapy.downloadermiddlewares.cookies.CookiesMiddleware": 700,
                    "scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware": 750,
                    "scrapy.downloadermiddlewares.stats.DownloaderStats": 850,
                    "scrapy.downloadermiddlewares.httpcache.HttpCacheMiddleware": 900,
                },
            },
        ),
    ),
    "DOWNLOADER_STATS": Setting(
        type=SettingType.BOOL,
        default_value=VersionedValue(True),
    ),
    "DUPEFILTER_CLASS": Setting(
        type=SettingType.OBJ,
        default_value=VersionedValue("scrapy.dupefilters.RFPDupeFilter"),
    ),
    "EDITOR": Setting(
        type=SettingType.STR,
        # Default set as unknown because it can vary by system.
        default_value=UNKNOWN_SETTING_VALUE,
    ),
    "EXTENSIONS": Setting(
        type=SettingType.BASED_COMP_PRIO_DICT,
        default_value=VersionedValue({}),
    ),
    "EXTENSIONS_BASE": Setting(
        default_value=VersionedValue(
            {
                "scrapy.extensions.corestats.CoreStats": 0,
                "scrapy.extensions.telnet.TelnetConsole": 0,
                "scrapy.extensions.memusage.MemoryUsage": 0,
                "scrapy.extensions.memdebug.MemoryDebugger": 0,
                "scrapy.extensions.closespider.CloseSpider": 0,
                "scrapy.extensions.feedexport.FeedExporter": 0,
                "scrapy.extensions.logstats.LogStats": 0,
                "scrapy.extensions.spiderstate.SpiderState": 0,
                "scrapy.extensions.throttle.AutoThrottle": 0,
            },
        ),
    ),
    "FEED_EXPORT_BATCH_ITEM_COUNT": Setting(
        type=SettingType.INT,
        default_value=VersionedValue(0),
        versioning=Versioning(added_in=Version("2.3.0")),
    ),
    "FEED_EXPORT_ENCODING": Setting(
        type=SettingType.OPT_STR,
        default_value=VersionedValue(
            history={
                UNKNOWN_FUTURE_VERSION: "utf-8",
                UNKNOWN_UNSUPPORTED_VERSION: None,
            },
        ),
    ),
    "FEED_EXPORT_FIELDS": Setting(
        type=SettingType.DICT_OR_LIST,
        default_value=VersionedValue(None),
    ),
    "FEED_EXPORT_INDENT": Setting(
        type=SettingType.OPT_INT,
        default_value=VersionedValue(0),
    ),
    "FEED_EXPORTERS": Setting(
        type=SettingType.BASED_OBJ_DICT,
        default_value=VersionedValue({}),
    ),
    "FEED_EXPORTERS_BASE": Setting(
        default_value=VersionedValue(
            history={
                Version("2.7.0"): {
                    "json": "scrapy.exporters.JsonItemExporter",
                    "jsonlines": "scrapy.exporters.JsonLinesItemExporter",
                    "jsonl": "scrapy.exporters.JsonLinesItemExporter",  # added
                    "jl": "scrapy.exporters.JsonLinesItemExporter",
                    "csv": "scrapy.exporters.CsvItemExporter",
                    "xml": "scrapy.exporters.XmlItemExporter",
                    "marshal": "scrapy.exporters.MarshalItemExporter",
                    "pickle": "scrapy.exporters.PickleItemExporter",
                },
                UNKNOWN_UNSUPPORTED_VERSION: {
                    "json": "scrapy.exporters.JsonItemExporter",
                    "jsonlines": "scrapy.exporters.JsonLinesItemExporter",
                    "jl": "scrapy.exporters.JsonLinesItemExporter",
                    "csv": "scrapy.exporters.CsvItemExporter",
                    "xml": "scrapy.exporters.XmlItemExporter",
                    "marshal": "scrapy.exporters.MarshalItemExporter",
                    "pickle": "scrapy.exporters.PickleItemExporter",
                },
            },
        ),
    ),
    "FEED_STORAGE_FTP_ACTIVE": Setting(
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
    ),
    "FEED_STORAGE_GCS_ACL": Setting(
        type=SettingType.OPT_STR,
        default_value=VersionedValue(""),
        versioning=Versioning(added_in=Version("2.3.0")),
    ),
    "FEED_STORAGE_S3_ACL": Setting(
        type=SettingType.OPT_STR,
        default_value=VersionedValue(""),
    ),
    "FEED_STORE_EMPTY": Setting(
        type=SettingType.BOOL,
        default_value=VersionedValue(True),
    ),
    "FEED_STORAGES": Setting(
        type=SettingType.BASED_OBJ_DICT,
        default_value=VersionedValue({}),
    ),
    "FEED_STORAGES_BASE": Setting(
        default_value=VersionedValue(
            history={
                Version("2.3.0"): {
                    "": "scrapy.extensions.feedexport.FileFeedStorage",
                    "file": "scrapy.extensions.feedexport.FileFeedStorage",
                    "ftp": "scrapy.extensions.feedexport.FTPFeedStorage",
                    "gs": "scrapy.extensions.feedexport.GCSFeedStorage",  # added
                    "s3": "scrapy.extensions.feedexport.S3FeedStorage",
                    "stdout": "scrapy.extensions.feedexport.StdoutFeedStorage",
                },
                UNKNOWN_UNSUPPORTED_VERSION: {
                    "": "scrapy.extensions.feedexport.FileFeedStorage",
                    "file": "scrapy.extensions.feedexport.FileFeedStorage",
                    "ftp": "scrapy.extensions.feedexport.FTPFeedStorage",
                    "s3": "scrapy.extensions.feedexport.S3FeedStorage",
                    "stdout": "scrapy.extensions.feedexport.StdoutFeedStorage",
                },
            },
        ),
    ),
    "FEED_TEMPDIR": Setting(
        type=SettingType.OPT_PATH,
        default_value=VersionedValue(None),
    ),
    "FEED_URI_PARAMS": Setting(
        type=SettingType.OPT_CALLABLE,
        default_value=VersionedValue(None),
    ),
    "FEEDS": Setting(
        type=SettingType.DICT,
        default_value=VersionedValue({}),
        versioning=Versioning(added_in=Version("2.1.0")),
    ),
    "FILES_STORE_GCS_ACL": Setting(
        type=SettingType.OPT_STR,
        default_value=VersionedValue(""),
    ),
    "FILES_STORE_S3_ACL": Setting(
        type=SettingType.OPT_STR,
        default_value=VersionedValue("private"),
    ),
    "FORCE_CRAWLER_PROCESS": Setting(
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
        is_pre_crawler=True,
        versioning=Versioning(added_in=Version("2.14.0")),
    ),
    "FTP_PASSIVE_MODE": Setting(
        type=SettingType.BOOL,
        default_value=VersionedValue(True),
    ),
    "FTP_PASSWORD": Setting(
        type=SettingType.OPT_STR,
        default_value=VersionedValue("guest"),
        is_secret=True,
    ),
    "FTP_USER": Setting(
        type=SettingType.OPT_STR,
        default_value=VersionedValue("anonymous"),
    ),
    "GCS_PROJECT_ID": Setting(
        type=SettingType.OPT_STR,
        default_value=VersionedValue(None),
        versioning=Versioning(added_in=Version("2.3.0")),
    ),
    "HTTP2_MAX_FRAME_SIZE": Setting(
        type=SettingType.INT,
        default_value=VersionedValue(16384),
        versioning=Versioning(added_in=Version("2.18.0")),
    ),
    "HTTPAUTH_DOMAIN": Setting(
        type=SettingType.OPT_STR,
        default_value=VersionedValue(None),
        versioning=Versioning(added_in=Version("2.17.0")),
    ),
    "HTTPAUTH_PASS": Setting(
        type=SettingType.OPT_STR,
        default_value=VersionedValue(""),
        versioning=Versioning(added_in=Version("2.17.0")),
    ),
    "HTTPAUTH_USER": Setting(
        type=SettingType.OPT_STR,
        default_value=VersionedValue(""),
        versioning=Versioning(added_in=Version("2.17.0")),
    ),
    "HTTPCACHE_ALWAYS_STORE": Setting(
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
    ),
    "HTTPCACHE_DBM_MODULE": Setting(
        type=SettingType.OPT_STR,
        default_value=VersionedValue("dbm"),
    ),
    "HTTPCACHE_DIR": Setting(
        type=SettingType.OPT_PATH,
        default_value=VersionedValue("httpcache"),
    ),
    "HTTPCACHE_ENABLED": Setting(
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
    ),
    "HTTPCACHE_EXPIRATION_SECS": Setting(
        type=SettingType.INT,
        default_value=VersionedValue(0),
    ),
    "HTTPCACHE_GZIP": Setting(
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
    ),
    "HTTPCACHE_IGNORE_HTTP_CODES": Setting(
        type=SettingType.LIST,
        default_value=VersionedValue([]),
    ),
    "HTTPCACHE_IGNORE_MISSING": Setting(
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
    ),
    "HTTPCACHE_IGNORE_RESPONSE_CACHE_CONTROLS": Setting(
        type=SettingType.LIST,
        default_value=VersionedValue([]),
    ),
    "HTTPCACHE_IGNORE_SCHEMES": Setting(
        type=SettingType.LIST,
        default_value=VersionedValue(["file"]),
    ),
    "HTTPCACHE_POLICY": Setting(
        type=SettingType.OBJ,
        default_value=VersionedValue("scrapy.extensions.httpcache.DummyPolicy"),
    ),
    "HTTPCACHE_STORAGE": Setting(
        type=SettingType.OBJ,
        default_value=VersionedValue(
            "scrapy.extensions.httpcache.FilesystemCacheStorage",
        ),
    ),
    "HTTPPROXY_AUTH_ENCODING": Setting(
        type=SettingType.OPT_STR,
        default_value=VersionedValue("latin-1"),
    ),
    "HTTPPROXY_ENABLED": Setting(
        type=SettingType.BOOL,
        default_value=VersionedValue(True),
    ),
    "HTTPX_HTTP2_ENABLED": Setting(
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
        versioning=Versioning(added_in=Version("2.17.0")),
    ),
    "IMAGES_STORE_GCS_ACL": Setting(
        type=SettingType.OPT_STR,
        default_value=VersionedValue(""),
    ),
    "IMAGES_STORE_S3_ACL": Setting(
        type=SettingType.OPT_STR,
        default_value=VersionedValue("private"),
    ),
    "ITEM_PIPELINES": Setting(
        type=SettingType.BASED_COMP_PRIO_DICT,
        default_value=VersionedValue({}),
    ),
    "ITEM_PIPELINES_BASE": Setting(default_value=VersionedValue({})),
    "ITEM_PROCESSOR": Setting(
        type=SettingType.OBJ,
        default_value=VersionedValue("scrapy.pipelines.ItemPipelineManager"),
    ),
    "JOBDIR": Setting(type=SettingType.OPT_PATH, default_value=VersionedValue(None)),
    "LOG_COLOR": Setting(
        type=SettingType.BOOL,
        default_value=VersionedValue(True),
        versioning=Versioning(added_in=Version("2.19.0")),
    ),
    "LOG_DATEFORMAT": Setting(
        type=SettingType.STR,
        default_value=VersionedValue("%Y-%m-%d %H:%M:%S"),
    ),
    "LOG_ENABLED": Setting(type=SettingType.BOOL, default_value=VersionedValue(True)),
    "LOG_INSTALL_ROOT_HANDLER": Setting(
        type=SettingType.BOOL,
        default_value=VersionedValue(True),
        versioning=Versioning(added_in=Version("2.19.0")),
    ),
    "LOG_ENCODING": Setting(
        type=SettingType.STR,
        default_value=VersionedValue("utf-8"),
    ),
    "LOG_FILE": Setting(type=SettingType.OPT_PATH, default_value=VersionedValue(None)),
    "LOG_FILE_APPEND": Setting(
        type=SettingType.BOOL,
        default_value=VersionedValue(True),
        versioning=Versioning(added_in=Version("2.6.0")),
    ),
    "LOG_FORMAT": Setting(
        type=SettingType.STR,
        default_value=VersionedValue(
            "%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        ),
    ),
    "LOG_FORMATTER": Setting(
        type=SettingType.OBJ,
        default_value=VersionedValue("scrapy.logformatter.LogFormatter"),
    ),
    "LOG_LEVEL": Setting(
        type=SettingType.LOG_LEVEL,
        default_value=VersionedValue("DEBUG"),
    ),
    "LOG_SHORT_NAMES": Setting(
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
    ),
    "LOG_STDOUT": Setting(type=SettingType.BOOL, default_value=VersionedValue(False)),
    "LOG_VERSIONS": Setting(
        type=SettingType.LIST,
        default_value=VersionedValue(
            [
                "lxml",
                "libxml2",
                "cssselect",
                "parsel",
                "w3lib",
                "Twisted",
                "Python",
                "pyOpenSSL",
                "cryptography",
                "Platform",
            ],
        ),
        versioning=Versioning(added_in=Version("2.13.0")),
    ),
    "LOGSTATS_INTERVAL": Setting(
        type=SettingType.FLOAT,
        default_value=VersionedValue(60.0),
    ),
    "MAIL_FROM": Setting(
        type=SettingType.OPT_STR,
        default_value=VersionedValue("scrapy@localhost"),
    ),
    "MAIL_HOST": Setting(
        type=SettingType.OPT_STR,
        default_value=VersionedValue("localhost"),
    ),
    "MAIL_PASS": Setting(
        type=SettingType.OPT_STR, default_value=VersionedValue(None), is_secret=True
    ),
    "MAIL_PORT": Setting(type=SettingType.OPT_STR, default_value=VersionedValue(25)),
    "MAIL_USER": Setting(type=SettingType.OPT_STR, default_value=VersionedValue(None)),
    "MEMDEBUG_ENABLED": Setting(
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
    ),
    "MEMUSAGE_CHECK_INTERVAL_SECONDS": Setting(
        type=SettingType.FLOAT,
        default_value=VersionedValue(60.0),
    ),
    "MEMUSAGE_ENABLED": Setting(
        type=SettingType.BOOL,
        default_value=VersionedValue(True),
    ),
    "MEMUSAGE_LIMIT_MB": Setting(type=SettingType.INT, default_value=VersionedValue(0)),
    "MEMUSAGE_WARNING_MB": Setting(
        type=SettingType.INT,
        default_value=VersionedValue(0),
    ),
    "METAREFRESH_ENABLED": Setting(
        type=SettingType.BOOL,
        default_value=VersionedValue(True),
    ),
    "METAREFRESH_IGNORE_TAGS": Setting(
        type=SettingType.LIST,
        default_value=VersionedValue(["noscript"]),
    ),
    "METAREFRESH_MAXDELAY": Setting(
        type=SettingType.INT,
        default_value=VersionedValue(100),
    ),
    "NEWSPIDER_MODULE": Setting(type=SettingType.STR, default_value=VersionedValue("")),
    "PERIODIC_LOG_DELTA": Setting(
        type=SettingType.PERIODIC_LOG_CONFIG,
        default_value=VersionedValue(None),
        versioning=Versioning(added_in=Version("2.11.0")),
    ),
    "PERIODIC_LOG_STATS": Setting(
        type=SettingType.PERIODIC_LOG_CONFIG,
        default_value=VersionedValue(None),
        versioning=Versioning(added_in=Version("2.11.0")),
    ),
    "PERIODIC_LOG_TIMING_ENABLED": Setting(
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
        versioning=Versioning(added_in=Version("2.11.0")),
    ),
    "REACTOR_THREADPOOL_MAXSIZE": Setting(
        type=SettingType.INT,
        default_value=VersionedValue(10),
        is_pre_crawler=True,
    ),
    "REDIRECT_ENABLED": Setting(
        type=SettingType.BOOL,
        default_value=VersionedValue(True),
    ),
    "REDIRECT_MAX_TIMES": Setting(
        type=SettingType.INT,
        default_value=VersionedValue(20),
    ),
    "REDIRECT_PRIORITY_ADJUST": Setting(
        type=SettingType.INT,
        default_value=VersionedValue(2),
    ),
    "REFERER_ENABLED": Setting(
        type=SettingType.BOOL,
        default_value=VersionedValue(True),
    ),
    "REFERRER_POLICY": Setting(
        type=SettingType.OBJ,
        default_value=VersionedValue(
            "scrapy.spidermiddlewares.referer.DefaultReferrerPolicy",
        ),
    ),
    "REFERRER_POLICIES": Setting(
        type=SettingType.DICT,
        default_value=VersionedValue({}),
        versioning=Versioning(added_in=Version("2.15.0")),
    ),
    "REMOTE_CONTROL_ENABLED": Setting(
        type=SettingType.BOOL,
        default_value=VersionedValue(True),
        versioning=Versioning(added_in=Version("2.19.0")),
    ),
    "REMOTE_CONTROL_JOBS_DIR": Setting(
        type=SettingType.OPT_PATH,
        default_value=VersionedValue(None),
        versioning=Versioning(added_in=Version("2.19.0")),
    ),
    "REMOTE_CONTROL_TIMEOUT_DEFAULT": Setting(
        type=SettingType.FLOAT,
        default_value=VersionedValue(30.0),
        versioning=Versioning(added_in=Version("2.19.0")),
    ),
    "REMOTE_CONTROL_TIMEOUT_MAX": Setting(
        type=SettingType.FLOAT,
        default_value=VersionedValue(600.0),
        versioning=Versioning(added_in=Version("2.19.0")),
    ),
    "REMOTE_CONTROL_OUTPUT_MAX_BYTES": Setting(
        type=SettingType.INT,
        default_value=VersionedValue(64 * 1024),
        versioning=Versioning(added_in=Version("2.19.0")),
    ),
    "REMOTE_CONTROL_TRACEBACK_MAX_BYTES": Setting(
        type=SettingType.INT,
        default_value=VersionedValue(16 * 1024),
        versioning=Versioning(added_in=Version("2.19.0")),
    ),
    "REQUEST_FINGERPRINTER_CLASS": Setting(
        type=SettingType.OBJ,
        default_value=VersionedValue("scrapy.utils.request.RequestFingerprinter"),
        versioning=Versioning(added_in=Version("2.7.0")),
    ),
    "RETRY_ENABLED": Setting(type=SettingType.BOOL, default_value=VersionedValue(True)),
    "RETRY_EXCEPTIONS": Setting(
        type=SettingType.LIST,
        default_value=VersionedValue(
            [
                "twisted.internet.defer.TimeoutError",
                "twisted.internet.error.TimeoutError",
                "twisted.internet.error.DNSLookupError",
                "twisted.internet.error.ConnectionRefusedError",
                "twisted.internet.error.ConnectionDone",
                "twisted.internet.error.ConnectError",
                "twisted.internet.error.ConnectionLost",
                "twisted.internet.error.TCPTimedOutError",
                "twisted.web.client.ResponseFailed",
                # OSError is raised by the HttpCompression middleware when trying to
                # decompress an empty response
                OSError,
                "scrapy.core.downloader.handlers.http11.TunnelError",
            ],
        ),
        versioning=Versioning(added_in=Version("2.10.0")),
    ),
    "RETRY_GIVE_UP_LOG_LEVEL": Setting(
        type=SettingType.LOG_LEVEL,
        default_value=VersionedValue("ERROR"),
        versioning=Versioning(added_in=Version("2.17.0")),
    ),
    "RETRY_HTTP_CODES": Setting(
        type=SettingType.LIST,
        default_value=VersionedValue([500, 502, 503, 504, 522, 524, 408, 429]),
    ),
    "RETRY_PRIORITY_ADJUST": Setting(
        type=SettingType.INT,
        default_value=VersionedValue(-1),
    ),
    "RETRY_TIMES": Setting(type=SettingType.INT, default_value=VersionedValue(2)),
    "ROBOTSTXT_OBEY": Setting(
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
    ),
    "ROBOTSTXT_PARSER": Setting(
        type=SettingType.OBJ,
        default_value=VersionedValue("scrapy.robotstxt.ProtegoRobotParser"),
    ),
    "ROBOTSTXT_USER_AGENT": Setting(
        type=SettingType.OPT_STR,
        default_value=VersionedValue(None),
    ),
    "SCHEDULER": Setting(
        type=SettingType.OBJ,
        default_value=VersionedValue("scrapy.core.scheduler.Scheduler"),
    ),
    "SCHEDULER_DEBUG": Setting(
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
    ),
    "SCHEDULER_DISK_QUEUE": Setting(
        type=SettingType.OBJ,
        default_value=VersionedValue("scrapy.squeues.PickleLifoDiskQueue"),
    ),
    "SCHEDULER_MEMORY_QUEUE": Setting(
        type=SettingType.OBJ,
        default_value=VersionedValue("scrapy.squeues.LifoMemoryQueue"),
    ),
    "SCHEDULER_PRIORITY_QUEUE": Setting(
        type=SettingType.OBJ,
        default_value=VersionedValue("scrapy.pqueues.ScrapyPriorityQueue"),
    ),
    "SCHEDULER_START_DISK_QUEUE": Setting(
        type=SettingType.OBJ,
        default_value=VersionedValue("scrapy.squeues.PickleFifoDiskQueue"),
        versioning=Versioning(added_in=Version("2.13.0")),
    ),
    "SCHEDULER_START_MEMORY_QUEUE": Setting(
        type=SettingType.OBJ,
        default_value=VersionedValue("scrapy.squeues.FifoMemoryQueue"),
        versioning=Versioning(added_in=Version("2.13.0")),
    ),
    "SCRAPER_SLOT_MAX_ACTIVE_SIZE": Setting(
        type=SettingType.INT,
        default_value=VersionedValue(5000000),
    ),
    "SPIDER_CONTRACTS": Setting(
        type=SettingType.BASED_COMP_PRIO_DICT,
        default_value=VersionedValue({}),
    ),
    "SPIDER_CONTRACTS_BASE": Setting(
        default_value=VersionedValue(
            history={
                Version("2.12.0"): {
                    "scrapy.contracts.default.UrlContract": 1,
                    "scrapy.contracts.default.CallbackKeywordArgumentsContract": 1,
                    "scrapy.contracts.default.MetadataContract": 1,  # added
                    "scrapy.contracts.default.ReturnsContract": 2,
                    "scrapy.contracts.default.ScrapesContract": 3,
                },
                UNKNOWN_UNSUPPORTED_VERSION: {
                    "scrapy.contracts.default.UrlContract": 1,
                    "scrapy.contracts.default.CallbackKeywordArgumentsContract": 1,
                    "scrapy.contracts.default.ReturnsContract": 2,
                    "scrapy.contracts.default.ScrapesContract": 3,
                },
            },
        ),
    ),
    "SPIDER_LOADER_CLASS": Setting(
        type=SettingType.OBJ,
        default_value=VersionedValue("scrapy.spiderloader.SpiderLoader"),
        is_pre_crawler=True,
    ),
    "SPIDER_LOADER_WARN_ONLY": Setting(
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
        is_pre_crawler=True,
    ),
    "SPIDER_MIDDLEWARES": Setting(
        type=SettingType.BASED_COMP_PRIO_DICT,
        default_value=VersionedValue({}),
    ),
    "SPIDER_MIDDLEWARES_BASE": Setting(
        default_value=VersionedValue(
            history={
                Version("2.13.0"): {
                    "scrapy.spidermiddlewares.start.StartSpiderMiddleware": 25,  # added
                    "scrapy.spidermiddlewares.httperror.HttpErrorMiddleware": 50,
                    "scrapy.spidermiddlewares.referer.RefererMiddleware": 700,
                    "scrapy.spidermiddlewares.urllength.UrlLengthMiddleware": 800,
                    "scrapy.spidermiddlewares.depth.DepthMiddleware": 900,
                },
                Version("2.11.2"): {
                    "scrapy.spidermiddlewares.httperror.HttpErrorMiddleware": 50,
                    "scrapy.spidermiddlewares.referer.RefererMiddleware": 700,
                    "scrapy.spidermiddlewares.urllength.UrlLengthMiddleware": 800,
                    "scrapy.spidermiddlewares.depth.DepthMiddleware": 900,
                },
                UNKNOWN_UNSUPPORTED_VERSION: {
                    "scrapy.spidermiddlewares.httperror.HttpErrorMiddleware": 50,
                    "scrapy.spidermiddlewares.offsite.OffsiteMiddleware": 500,  # removed next
                    "scrapy.spidermiddlewares.referer.RefererMiddleware": 700,
                    "scrapy.spidermiddlewares.urllength.UrlLengthMiddleware": 800,
                    "scrapy.spidermiddlewares.depth.DepthMiddleware": 900,
                },
            },
        ),
    ),
    "SPIDER_MODULES": Setting(
        type=SettingType.LIST,
        default_value=VersionedValue([]),
        is_pre_crawler=True,
    ),
    "STATS_CLASS": Setting(
        type=SettingType.OBJ,
        default_value=VersionedValue("scrapy.statscollectors.MemoryStatsCollector"),
    ),
    "STATS_DUMP": Setting(type=SettingType.BOOL, default_value=VersionedValue(True)),
    "STATSMAILER_RCPTS": Setting(
        type=SettingType.LIST,
        default_value=VersionedValue([]),
    ),
    "TELNETCONSOLE_ENABLED": Setting(
        type=SettingType.BOOL,
        default_value=VersionedValue(1),
    ),
    "TELNETCONSOLE_HOST": Setting(
        type=SettingType.STR,
        default_value=VersionedValue("127.0.0.1"),
    ),
    "TELNETCONSOLE_PASSWORD": Setting(
        type=SettingType.OPT_STR,
        default_value=VersionedValue(None),
        is_secret=True,
    ),
    "TELNETCONSOLE_PORT": Setting(
        type=SettingType.LIST,
        default_value=VersionedValue([6023, 6073]),
    ),
    "TELNETCONSOLE_USERNAME": Setting(
        type=SettingType.STR,
        default_value=VersionedValue("scrapy"),
    ),
    "TEMPLATES_DIR": Setting(
        type=SettingType.OPT_PATH,
        # Default set as unknown because it can vary by system.
        default_value=UNKNOWN_SETTING_VALUE,
    ),
    "TWISTED_DNS_RESOLVER": Setting(
        type=SettingType.OBJ,
        default_value=VersionedValue("scrapy.resolver.CachingThreadedResolver"),
        is_pre_crawler=True,
        versioning=Versioning(added_in=Version("2.15.0")),
    ),
    "TWISTED_REACTOR_ENABLED": Setting(
        type=SettingType.BOOL,
        default_value=VersionedValue(True),
        is_pre_crawler=True,
        versioning=Versioning(added_in=Version("2.15.0")),
    ),
    "TWISTED_REACTOR": Setting(
        type=SettingType.OPT_OBJ,
        default_value=VersionedValue(
            history={
                Version(
                    "2.13.0",
                ): "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
                UNKNOWN_UNSUPPORTED_VERSION: None,
            },
        ),
        is_pre_crawler=True,
    ),
    "URLLENGTH_LIMIT": Setting(
        type=SettingType.INT,
        default_value=VersionedValue(2083),
    ),
    "USER_AGENT": Setting(
        type=SettingType.OPT_STR,
        # Default set as unknown because it depends on the installed version of Scrapy.
        default_value=UNKNOWN_SETTING_VALUE,
    ),
    "WARN_ON_GENERATOR_RETURN_VALUE": Setting(
        type=SettingType.BOOL,
        default_value=VersionedValue(True),
        versioning=Versioning(added_in=Version("2.13.0")),
    ),
    # Active (i.e. neither deprecated nor removed) Scrapy built-in settings
    # that are missing from the default_settings.py file, in alphabetical
    # order.
    "AWS_ACCESS_KEY_ID": Setting(
        type=SettingType.OPT_STR,
        default_value=VersionedValue(None),
    ),
    "AWS_ENDPOINT_URL": Setting(
        type=SettingType.OPT_STR,
        default_value=VersionedValue(None),
    ),
    "AWS_REGION_NAME": Setting(
        type=SettingType.OPT_STR,
        default_value=VersionedValue(None),
    ),
    "AWS_SECRET_ACCESS_KEY": Setting(
        type=SettingType.OPT_STR,
        default_value=VersionedValue(None),
        is_secret=True,
    ),
    "AWS_SESSION_TOKEN": Setting(
        type=SettingType.OPT_STR,
        default_value=VersionedValue(None),
        is_secret=True,
    ),
    "AWS_USE_SSL": Setting(type=SettingType.BOOL, default_value=VersionedValue(False)),
    "AWS_VERIFY": Setting(type=SettingType.BOOL, default_value=VersionedValue(False)),
    "CLOSESPIDER_PAGECOUNT_NO_ITEM": Setting(
        type=SettingType.INT,
        default_value=VersionedValue(0),
        versioning=Versioning(added_in=Version("2.12.0")),
    ),
    "CLOSESPIDER_TIMEOUT_NO_ITEM": Setting(
        type=SettingType.INT,
        default_value=VersionedValue(0),
        versioning=Versioning(added_in=Version("2.10.0")),
    ),
    "DOWNLOAD_SLOTS": Setting(
        type=SettingType.DICT,
        default_value=VersionedValue({}),
        versioning=Versioning(added_in=Version("2.9.0")),
    ),
    "DUPEFILTER_DEBUG": Setting(
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
    ),
    "FILES_EXPIRES": Setting(type=SettingType.INT, default_value=VersionedValue(0)),
    "FILES_RESULT_FIELD": Setting(
        type=SettingType.OPT_STR,
        default_value=VersionedValue(None),
    ),
    "FILES_STORE": Setting(
        type=SettingType.OPT_PATH,
        default_value=VersionedValue(None),
    ),
    "FILES_URLS_FIELD": Setting(
        type=SettingType.OPT_STR,
        default_value=VersionedValue(None),
    ),
    "HTTPERROR_ALLOW_ALL": Setting(
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
    ),
    "HTTPERROR_ALLOWED_CODES": Setting(
        type=SettingType.LIST,
        default_value=VersionedValue([]),
    ),
    "IMAGES_EXPIRES": Setting(type=SettingType.INT, default_value=VersionedValue(0)),
    "IMAGES_MIN_HEIGHT": Setting(type=SettingType.INT, default_value=VersionedValue(0)),
    "IMAGES_MIN_WIDTH": Setting(type=SettingType.INT, default_value=VersionedValue(0)),
    "IMAGES_RESULT_FIELD": Setting(
        type=SettingType.OPT_STR,
        default_value=VersionedValue(None),
    ),
    "IMAGES_STORE": Setting(
        type=SettingType.OPT_PATH,
        default_value=VersionedValue(None),
    ),
    "IMAGES_THUMBS": Setting(type=SettingType.DICT, default_value=VersionedValue({})),
    "IMAGES_URLS_FIELD": Setting(
        type=SettingType.OPT_STR,
        default_value=VersionedValue(None),
    ),
    "MAIL_TLS": Setting(type=SettingType.BOOL, default_value=VersionedValue(False)),
    "MAIL_SSL": Setting(type=SettingType.BOOL, default_value=VersionedValue(False)),
    "MEDIA_ALLOW_REDIRECTS": Setting(
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
    ),
    "META_COPY_WARN_SKIP_KEYS": Setting(
        type=SettingType.LIST,
        default_value=VersionedValue([]),
        versioning=Versioning(added_in=Version("2.18.0")),
    ),
    # Deprecated Scrapy built-in settings, in reverse deprecation order.
    "RANDOMIZE_DOWNLOAD_DELAY": Setting(
        type=SettingType.BOOL,
        default_value=VersionedValue(True),
        versioning=Versioning(
            deprecated_in=Version("2.19.0"),
            sunset_guidance=(
                "use DOWNLOAD_DELAY_JITTER instead, e.g. 0.5 for the ±50% that True "
                "meant, or 0 to disable"
            ),
        ),
    ),
    "CRAWLSPIDER_FOLLOW_LINKS": Setting(
        type=SettingType.BOOL,
        default_value=VersionedValue(True),
        versioning=Versioning(
            deprecated_in=Version("2.17.0"),
            sunset_guidance="set follow=False in your rules instead",
        ),
        discouraged_in=UNKNOWN_UNSUPPORTED_VERSION,
    ),
    "DNS_RESOLVER": Setting(
        type=SettingType.OBJ,
        default_value=VersionedValue("scrapy.resolver.CachingThreadedResolver"),
        is_pre_crawler=True,
        versioning=Versioning(
            deprecated_in=Version("2.15.0"),
            sunset_guidance="use TWISTED_DNS_RESOLVER instead",
        ),
    ),
    "DOWNLOADER_CLIENTCONTEXTFACTORY": Setting(
        type=SettingType.OBJ,
        default_value=VersionedValue(
            "scrapy.core.downloader.contextfactory.ScrapyClientContextFactory",
        ),
        versioning=Versioning(
            deprecated_in=Version("2.15.0"),
            sunset_guidance=(
                "use DOWNLOAD_VERIFY_CERTIFICATES if the setting was used to switch to "
                "BrowserLikeContextFactory, otherwise subclass the download handler"
            ),
        ),
    ),
    "DOWNLOADER_CLIENT_TLS_METHOD": Setting(
        type=SettingType.ENUM_STR,
        values=("TLS", "TLSv1.0", "TLSv1.1", "TLSv1.2"),
        default_value=VersionedValue("TLS"),
        versioning=Versioning(
            deprecated_in=Version("2.17.0"),
            sunset_guidance=(
                "use DOWNLOAD_TLS_MIN_VERSION and/or DOWNLOAD_TLS_MAX_VERSION instead"
            ),
        ),
    ),
    "MEMUSAGE_NOTIFY_MAIL": Setting(
        type=SettingType.LIST,
        default_value=VersionedValue([]),
        versioning=Versioning(
            deprecated_in=Version("2.15.0"),
            sunset_guidance=(
                "use the memusage_warning_reached and spider_closed signals instead"
            ),
        ),
        discouraged_in=UNKNOWN_UNSUPPORTED_VERSION,
    ),
    "CONCURRENT_REQUESTS_PER_IP": Setting(
        type=SettingType.INT,
        default_value=VersionedValue(0),
        versioning=Versioning(deprecated_in=Version("2.14.0")),
        replacement="CONCURRENT_REQUESTS_PER_DOMAIN",
        discouraged_in=UNKNOWN_UNSUPPORTED_VERSION,
    ),
    "FEED_FORMAT": Setting(
        type=SettingType.STR,
        default_value=VersionedValue("jsonlines"),
        versioning=Versioning(
            deprecated_in=Version("2.1.0"),
            sunset_guidance="use FEEDS instead",
        ),
    ),
    "FEED_URI": Setting(
        type=SettingType.OPT_STR,
        versioning=Versioning(
            deprecated_in=Version("2.1.0"),
            sunset_guidance="use FEEDS instead",
        ),
    ),
    # Removed Scrapy built-in settings, in reverse removal order.
    "MEMDEBUG_NOTIFY": Setting(
        type=SettingType.LIST,
        default_value=VersionedValue([]),
        versioning=Versioning(removed_in=Version("2.18.0")),
    ),
    "AJAXCRAWL_ENABLED": Setting(
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
        versioning=Versioning(
            added_in=Version("0.22.0"),
            deprecated_in=Version("2.13.0"),
            removed_in=Version("2.16.0"),
        ),
    ),
    "AJAXCRAWL_MAXSIZE": Setting(
        type=SettingType.INT,
        default_value=VersionedValue(32768),
        versioning=Versioning(
            added_in=Version("0.22.0"),
            deprecated_in=Version("2.13.0"),
            removed_in=Version("2.16.0"),
        ),
    ),
    "DOWNLOADER_HTTPCLIENTFACTORY": Setting(
        type=SettingType.OBJ,
        default_value=VersionedValue(
            "scrapy.core.downloader.webclient.ScrapyHTTPClientFactory",
        ),
        versioning=Versioning(
            deprecated_in=Version("2.13.0"),
            removed_in=Version("2.16.0"),
        ),
    ),
    "REQUEST_FINGERPRINTER_IMPLEMENTATION": Setting(
        type=SettingType.ENUM_STR,
        default_value=VersionedValue("SENTINEL"),
        values=("2.6", "2.7"),
        versioning=Versioning(
            added_in=Version("2.7.0"),
            deprecated_in=Version("2.12.0"),
            removed_in=Version("2.14.0"),
        ),
    ),
    "SPIDER_MANAGER_CLASS": Setting(
        type=SettingType.OBJ,
        versioning=Versioning(
            removed_in=Version("2.5.0"),
            deprecated_in=Version("1.0.0"),
        ),
    ),
    "LOG_UNSERIALIZABLE_REQUESTS": Setting(
        type=SettingType.BOOL,
        versioning=Versioning(
            removed_in=Version("2.1.0"),
            deprecated_in=UNKNOWN_UNSUPPORTED_VERSION,
        ),
        replacement="SCHEDULER_DEBUG",
    ),
    "REDIRECT_MAX_METAREFRESH_DELAY": Setting(
        type=SettingType.FLOAT,
        versioning=Versioning(
            removed_in=Version("2.1.0"),
            deprecated_in=UNKNOWN_UNSUPPORTED_VERSION,
        ),
        replacement="METAREFRESH_MAXDELAY",
    ),
    # scrapy-azure-exporter plugin settings, in order of appearance
    # in https://github.com/scrapy-plugins/scrapy-feedexporter-azure-storage
    "AZURE_CONNECTION_STRING": Setting(package="scrapy-azure-exporter", is_secret=True),
    "AZURE_ACCOUNT_URL_WITH_SAS_TOKEN": Setting(
        package="scrapy-azure-exporter", is_secret=True
    ),
    "AZURE_ACCOUNT_URL": Setting(package="scrapy-azure-exporter"),
    "AZURE_ACCOUNT_KEY": Setting(package="scrapy-azure-exporter", is_secret=True),
    # scrapy-deltafetch plugin settings, in order of appearance in
    # https://github.com/scrapy-plugins/scrapy-deltafetch#usage
    "DELTAFETCH_ENABLED": Setting(package="scrapy-deltafetch", type=SettingType.BOOL),
    "DELTAFETCH_DIR": Setting(
        package="scrapy-deltafetch",
        type=SettingType.STR,
        default_value=VersionedValue("deltafetch"),
    ),
    "DELTAFETCH_RESET": Setting(
        package="scrapy-deltafetch",
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
    ),
    # scrapy-feedexporter-dropbox plugin settings, in order of appearance in
    # https://github.com/scrapy-plugins/scrapy-feedexporter-dropbox
    "DROPBOX_API_TOKEN": Setting(package="scrapy-feedexporter-dropbox", is_secret=True),
    # scrapy-frontera plugin settings, in order of appearance in
    # https://github.com/scrapinghub/scrapy-frontera#usage-and-features
    "FRONTERA_SCHEDULER_START_REQUESTS_TO_FRONTIER": Setting(package="scrapy-frontera"),
    "FRONTERA_SCHEDULER_REQUEST_CALLBACKS_TO_FRONTIER": Setting(
        package="scrapy-frontera",
    ),
    "FRONTERA_SCHEDULER_STATE_ATTRIBUTES": Setting(package="scrapy-frontera"),
    "FRONTERA_SCHEDULER_CALLBACK_SLOT_PREFIX_MAP": Setting(package="scrapy-frontera"),
    "BACKEND": Setting(package="scrapy-frontera"),
    # scrapy-feedexporter-google-drive plugin settings, in order of appearance
    # in https://github.com/scrapy-plugins/scrapy-feedexporter-google-drive
    "GDRIVE_SERVICE_ACCOUNT_CREDENTIALS_JSON": Setting(
        package="scrapy-feedexporter-google-drive",
        is_secret=True,
    ),
    # scrapy-feedexporter-google-sheets plugin settings, in order of appearance
    # in https://github.com/scrapy-plugins/scrapy-feedexporter-google-sheets
    "GOOGLE_CREDENTIALS": Setting(
        package="scrapy-feedexporter-google-sheets", is_secret=True
    ),
    # scrapy-fieldstats plugin settings, in order of appearance in
    # https://github.com/stummjr/scrapy-fieldstats
    "FIELDSTATS_ENABLED": Setting(
        package="scrapy-fieldstats",
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
    ),
    "FIELDSTATS_COUNTS_ONLY": Setting(
        package="scrapy-fieldstats",
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
    ),
    "FIELDSTATS_SKIP_NONE": Setting(
        package="scrapy-fieldstats",
        type=SettingType.BOOL,
        default_value=VersionedValue(True),
    ),
    "FIELDSTATS_ADD_TO_STATS": Setting(
        package="scrapy-fieldstats",
        type=SettingType.BOOL,
        default_value=VersionedValue(True),
    ),
    # hcf-backend plugin settings, in order of appearance in
    # https://github.com/scrapinghub/hcf-backend/blob/master/hcf_backend/backend.py
    "HCF_CONSUMER_MAX_REQUESTS": Setting(package="hcf-backend"),
    "HCF_CONSUMER_MAX_BATCHES": Setting(package="hcf-backend"),
    "MAX_NEXT_REQUESTS": Setting(package="hcf-backend"),
    "HCF_AUTH": Setting(package="hcf-backend", is_secret=True),
    "HCF_PROJECT_ID": Setting(package="hcf-backend"),
    "HCF_PRODUCER_FRONTIER": Setting(package="hcf-backend"),
    "HCF_PRODUCER_SLOT_PREFIX": Setting(package="hcf-backend"),
    "HCF_PRODUCER_NUMBER_OF_SLOTS": Setting(package="hcf-backend"),
    "HCF_PRODUCER_BATCH_SIZE": Setting(package="hcf-backend"),
    "HCF_CONSUMER_FRONTIER": Setting(package="hcf-backend"),
    "HCF_CONSUMER_SLOT": Setting(package="hcf-backend"),
    "HCF_CONSUMER_DONT_DELETE_REQUESTS": Setting(package="hcf-backend"),
    "HCF_CONSUMER_DELETE_BATCHES_ON_STOP": Setting(package="hcf-backend"),
    # scrapy-incremental plugin settings, in order of appearance in
    # https://github.com/scrapy-plugins/scrapy-incremental
    "SCRAPYCLOUD_API_KEY": Setting(package="scrapy-incremental", is_secret=True),
    "SCRAPYCLOUD_PROJECT_ID": Setting(package="scrapy-incremental"),
    "INCREMENTAL_PIPELINE_ITEM_UNIQUE_FIELD": Setting(package="scrapy-incremental"),
    "INCREMENTAL_PIPELINE_BATCH_SIZE": Setting(package="scrapy-incremental"),
    # scrapy-feedexporter-onedrive plugin settings, in order of appearance in
    # https://github.com/scrapy-plugins/scrapy-feedexporter-onedrive
    "ONEDRIVE_ACCESS_TOKEN": Setting(
        package="scrapy-feedexporter-onedrive", is_secret=True
    ),
    # scrapy-playwright plugin settings, in order of appearance in
    # https://github.com/scrapy-plugins/scrapy-playwright#supported-settings
    "PLAYWRIGHT_BROWSER_TYPE": Setting(
        package="scrapy-playwright",
        type=SettingType.STR,
        default_value=VersionedValue("chromium"),
    ),
    "PLAYWRIGHT_LAUNCH_OPTIONS": Setting(
        package="scrapy-playwright",
        type=SettingType.DICT,
        default_value=VersionedValue({}),
    ),
    "PLAYWRIGHT_BROWSER_PROVIDER": Setting(
        package="scrapy-playwright",
        type=SettingType.OBJ,
        default_value=VersionedValue(
            "scrapy_playwright.provider.PlaywrightBrowserProvider",
        ),
        versioning=Versioning(added_in=Version("0.0.48")),
    ),
    "PLAYWRIGHT_CDP_URL": Setting(
        package="scrapy-playwright",
        type=SettingType.OPT_STR,
        default_value=VersionedValue(None),
        versioning=Versioning(added_in=Version("0.0.32")),
    ),
    "PLAYWRIGHT_CDP_KWARGS": Setting(
        package="scrapy-playwright",
        type=SettingType.DICT,
        default_value=VersionedValue({}),
        versioning=Versioning(added_in=Version("0.0.32")),
    ),
    "PLAYWRIGHT_CONNECT_URL": Setting(
        package="scrapy-playwright",
        type=SettingType.OPT_STR,
        default_value=VersionedValue(None),
        versioning=Versioning(added_in=Version("0.0.38")),
    ),
    "PLAYWRIGHT_CONNECT_KWARGS": Setting(
        package="scrapy-playwright",
        type=SettingType.DICT,
        default_value=VersionedValue({}),
        versioning=Versioning(added_in=Version("0.0.38")),
    ),
    "PLAYWRIGHT_CONTEXTS": Setting(
        package="scrapy-playwright",
        type=SettingType.DICT,
        default_value=VersionedValue({}),
        versioning=Versioning(added_in=Version("0.0.4")),
    ),
    "PLAYWRIGHT_MAX_CONTEXTS": Setting(
        package="scrapy-playwright",
        type=SettingType.OPT_INT,
        default_value=VersionedValue(None),
        versioning=Versioning(added_in=Version("0.0.17")),
    ),
    "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": Setting(
        package="scrapy-playwright",
        type=SettingType.FLOAT,
        default_value=VersionedValue(None),
    ),
    "PLAYWRIGHT_DOWNLOAD_TIMEOUT": Setting(
        package="scrapy-playwright",
        type=SettingType.INT,
        default_value=VersionedValue(30000),
        versioning=Versioning(added_in=Version("0.0.47")),
    ),
    "PLAYWRIGHT_PROCESS_REQUEST_HEADERS": Setting(
        package="scrapy-playwright",
        type=SettingType.OPT_OBJ,
        default_value=VersionedValue("scrapy_playwright.headers.use_scrapy_headers"),
    ),
    "PLAYWRIGHT_RESTART_DISCONNECTED_BROWSER": Setting(
        package="scrapy-playwright",
        type=SettingType.BOOL,
        default_value=VersionedValue(True),
        versioning=Versioning(added_in=Version("0.0.39")),
    ),
    "PLAYWRIGHT_MAX_PAGES_PER_CONTEXT": Setting(
        package="scrapy-playwright",
        type=SettingType.INT,
        # Defaults to the value of CONCURRENT_REQUESTS.
        default_value=UNKNOWN_SETTING_VALUE,
        versioning=Versioning(added_in=Version("0.0.11")),
    ),
    "PLAYWRIGHT_ABORT_REQUEST": Setting(
        package="scrapy-playwright",
        type=SettingType.OPT_OBJ,
        default_value=VersionedValue(None),
        versioning=Versioning(added_in=Version("0.0.13")),
    ),
    "PLAYWRIGHT_CONTEXT_ARGS": Setting(
        package="scrapy-playwright",
        type=SettingType.DICT,
        versioning=Versioning(
            deprecated_in=Version("0.0.4"),
            removed_in=Version("0.0.15"),
            sunset_guidance=(
                'use PLAYWRIGHT_CONTEXTS instead, as the "default" context'
            ),
        ),
    ),
    # scrapy-poet plugin settings, in order of appearance in
    # https://scrapy-poet.readthedocs.io/en/stable/settings.html
    "SCRAPY_POET_CACHE": Setting(
        package="scrapy-poet",
        versioning=Versioning(added_in=Version("0.3.0")),
    ),
    "SCRAPY_POET_CACHE_ERRORS": Setting(
        package="scrapy-poet",
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
        versioning=Versioning(added_in=Version("0.3.0")),
    ),
    "SCRAPY_POET_DISCOVER": Setting(
        package="scrapy-poet",
        type=SettingType.LIST,
        default_value=VersionedValue([]),
        versioning=Versioning(added_in=Version("0.9.0")),
    ),
    "SCRAPY_POET_OVERRIDES": Setting(
        package="scrapy-poet",
        versioning=Versioning(
            deprecated_in=Version("0.9.0"),
            removed_in=Version("0.27.0"),
            sunset_guidance="use SCRAPY_POET_DISCOVER and/or SCRAPY_POET_RULES instead",
        ),
    ),
    "SCRAPY_POET_PROVIDERS": Setting(
        package="scrapy-poet",
        type=SettingType.COMP_PRIO_DICT,
        default_value=VersionedValue({}),
        versioning=Versioning(added_in=Version("0.1.0")),
    ),
    "SCRAPY_POET_REQUEST_FINGERPRINTER_BASE_CLASS": Setting(
        package="scrapy-poet",
        type=SettingType.OBJ,
        versioning=Versioning(added_in=Version("0.20.0")),
    ),
    "SCRAPY_POET_RULES": Setting(
        package="scrapy-poet",
        type=SettingType.LIST,
        versioning=Versioning(added_in=Version("0.9.0")),
    ),
    "SCRAPY_POET_TESTS_ADAPTER": Setting(
        package="scrapy-poet",
        type=SettingType.OPT_OBJ,
        default_value=VersionedValue(None),
        versioning=Versioning(added_in=Version("0.13.0")),
    ),
    "SCRAPY_POET_TESTS_DIR": Setting(
        package="scrapy-poet",
        type=SettingType.STR,
        default_value=VersionedValue("fixtures"),
        versioning=Versioning(added_in=Version("0.8.0")),
    ),
    "_SCRAPY_POET_SAVEFIXTURE": Setting(
        package="scrapy-poet",
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
        versioning=Versioning(added_in=Version("0.11.0")),
    ),
    # Removed scrapy-poet settings.
    "SCRAPY_POET_OVERRIDES_REGISTRY": Setting(
        package="scrapy-poet",
        versioning=Versioning(
            removed_in=Version("0.9.0"),
            removal_guidance="scrapy-poet uses web_poet.rules.RulesRegistry",
        ),
    ),
    "SCRAPY_POET_CACHE_GZIP": Setting(
        package="scrapy-poet",
        versioning=Versioning(removed_in=Version("0.14.0")),
    ),
    # scrapy-redis plugin settings, in order of appearance in
    # https://github.com/rmax/scrapy-redis/wiki/Usage
    "SCHEDULER_SERIALIZER": Setting(
        package="scrapy-redis",
        type=SettingType.OPT_OBJ,
        default_value=VersionedValue(None),
    ),
    "SCHEDULER_PERSIST": Setting(
        package="scrapy-redis",
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
    ),
    "SCHEDULER_FLUSH_ON_START": Setting(
        package="scrapy-redis",
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
    ),
    "SCHEDULER_QUEUE_CLASS": Setting(
        package="scrapy-redis",
        type=SettingType.OBJ,
        default_value=VersionedValue("scrapy_redis.queue.PriorityQueue"),
    ),
    "SCHEDULER_QUEUE_KEY": Setting(
        package="scrapy-redis",
        type=SettingType.STR,
        default_value=VersionedValue("%(spider)s:requests"),
    ),
    "SCHEDULER_DUPEFILTER_KEY": Setting(
        package="scrapy-redis",
        type=SettingType.STR,
        default_value=VersionedValue("%(spider)s:dupefilter"),
    ),
    "SCHEDULER_IDLE_BEFORE_CLOSE": Setting(
        package="scrapy-redis",
        type=SettingType.INT,
        default_value=VersionedValue(0),
    ),
    "REDIS_ITEMS_KEY": Setting(
        package="scrapy-redis",
        type=SettingType.STR,
        default_value=VersionedValue("%(spider)s:items"),
    ),
    "REDIS_ITEMS_SERIALIZER": Setting(
        package="scrapy-redis",
        type=SettingType.OPT_OBJ,
        default_value=VersionedValue(None),
    ),
    "REDIS_HOST": Setting(
        package="scrapy-redis",
        type=SettingType.OPT_STR,
        default_value=VersionedValue(None),
    ),
    "REDIS_PORT": Setting(
        package="scrapy-redis",
        type=SettingType.OPT_INT,
        default_value=VersionedValue(None),
    ),
    "REDIS_DB": Setting(package="scrapy-redis"),
    "REDIS_URL": Setting(
        package="scrapy-redis",
        type=SettingType.OPT_STR,
        default_value=VersionedValue(None),
    ),
    "REDIS_PARAMS": Setting(
        package="scrapy-redis",
        type=SettingType.DICT,
        default_value=VersionedValue(
            {
                "socket_timeout": 30,
                "socket_connect_timeout": 30,
                "retry_on_timeout": True,
                "encoding": "utf-8",
            }
        ),
    ),
    "REDIS_START_URLS_AS_SET": Setting(
        package="scrapy-redis",
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
    ),
    "REDIS_START_URLS_AS_ZSET": Setting(
        package="scrapy-redis",
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
    ),
    "REDIS_START_URLS_KEY": Setting(
        package="scrapy-redis",
        type=SettingType.STR,
        default_value=VersionedValue("%(name)s:start_urls"),
    ),
    "REDIS_START_URLS_BATCH_SIZE": Setting(
        package="scrapy-redis",
        type=SettingType.INT,
        versioning=Versioning(deprecated_in=Version("0.8.0")),
        replacement="CONCURRENT_REQUESTS",
    ),
    "REDIS_ENCODING": Setting(
        package="scrapy-redis",
        type=SettingType.STR,
        default_value=VersionedValue("utf-8"),
    ),
    "REDIS_DECODE_RESPONSES": Setting(package="scrapy-redis"),
    "REDIS_KEY_CHECK_INTERVAL": Setting(package="scrapy-redis"),
    "MAX_IDLE_TIME_BEFORE_CLOSE": Setting(
        package="scrapy-redis",
        type=SettingType.INT,
        default_value=VersionedValue(0),
        versioning=Versioning(added_in=Version("0.7.2")),
    ),
    # scrapyrt plugin settings, in order of appearance in
    # https://scrapyrt.readthedocs.io/en/latest/api.html#available-settings
    "SERVICE_ROOT": Setting(
        package="scrapyrt",
        type=SettingType.OBJ,
        default_value=VersionedValue("scrapyrt.resources.RealtimeApi"),
    ),
    "CRAWL_MANAGER": Setting(
        package="scrapyrt",
        type=SettingType.OBJ,
        default_value=VersionedValue("scrapyrt.core.CrawlManager"),
    ),
    "RESOURCES": Setting(
        package="scrapyrt",
        type=SettingType.DICT,
        default_value=VersionedValue(
            {"crawl.json": "scrapyrt.resources.CrawlResource"}
        ),
    ),
    "LOG_DIR": Setting(
        package="scrapyrt",
        type=SettingType.STR,
        default_value=VersionedValue("logs"),
    ),
    "TIMEOUT_LIMIT": Setting(
        package="scrapyrt",
        type=SettingType.INT,
        default_value=VersionedValue(1000),
    ),
    "DEBUG": Setting(
        package="scrapyrt",
        type=SettingType.BOOL,
        default_value=VersionedValue(True),
    ),
    "PROJECT_SETTINGS": Setting(
        package="scrapyrt",
        type=SettingType.OPT_STR,
        default_value=VersionedValue(None),
    ),
    "DEFAULT_ERRBACK_NAME": Setting(
        package="scrapyrt",
        type=SettingType.OPT_STR,
        default_value=VersionedValue(None),
        versioning=Versioning(added_in=Version("0.16.0")),
    ),
    "SPIDER_LOG_FILE_TIMEFORMAT": Setting(
        package="scrapyrt",
        type=SettingType.STR,
        default_value=VersionedValue("%Y-%m-%dT%H%M%S.%f"),
        versioning=Versioning(added_in=Version("0.10.0")),
    ),
    # scrapy-settings-log plugin settings, in order of appearance in
    # https://github.com/scrapy-plugins/scrapy-settings-log
    "SETTINGS_LOGGING_ENABLED": Setting(
        package="scrapy-settings-log",
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
    ),
    "SETTINGS_LOGGING_REGEX": Setting(
        package="scrapy-settings-log",
        type=SettingType.OPT_STR,
        default_value=VersionedValue(None),
    ),
    "SETTINGS_LOGGING_INDENT": Setting(
        package="scrapy-settings-log",
        type=SettingType.OPT_INT,
        default_value=VersionedValue(None),
    ),
    "MASKED_SENSITIVE_SETTINGS_ENABLED": Setting(
        package="scrapy-settings-log",
        type=SettingType.BOOL,
        default_value=VersionedValue(True),
    ),
    "MASKED_SENSITIVE_SETTINGS_REGEX_LIST": Setting(
        package="scrapy-settings-log",
        type=SettingType.LIST,
        default_value=VersionedValue(
            [
                r"(?i).*(api[\W_]*key).*",
                r"(?i).*(AWS[\W_]*(SECRET[\W_]*)?(ACCESS)?[\W_]*(KEY|ACCESS[\W_]*KEY))",
                r"(?i).*([\W_]*password[\W_]*).*",
            ]
        ),
    ),
    # scrapy-feedexporter-sftp plugin settings, in order of appearance in
    # https://github.com/scrapy-plugins/scrapy-feedexporter-sftp
    "FEED_STORAGE_SFTP_PKEY": Setting(
        package="scrapy-feedexporter-sftp", is_secret=True
    ),
    # scrapy-splash plugin settings, in order of appearance in
    # https://github.com/scrapy-plugins/scrapy-splash#configuration
    "SPLASH_URL": Setting(package="scrapy-splash"),
    "SPLASH_COOKIES_DEBUG": Setting(
        package="scrapy-splash",
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
    ),
    "SPLASH_LOG_400": Setting(
        package="scrapy-splash",
        type=SettingType.BOOL,
        default_value=VersionedValue(True),
    ),
    "SPLASH_SLOT_POLICY": Setting(package="scrapy-splash"),
    "SPLASH_USER": Setting(package="scrapy-splash"),
    "SPLASH_PASS": Setting(package="scrapy-splash", is_secret=True),
    "SCRAPY_SPLASH_REQUEST_FINGERPRINTER_BASE_CLASS": Setting(package="scrapy-splash"),
    # spidermon plugin settings, in order of appearance in the docs:
    # https://spidermon.readthedocs.io/en/latest/settings.html
    "SPIDERMON_ENABLED": Setting(package="spidermon", type=SettingType.BOOL),
    "SPIDERMON_EXPRESSIONS_MONITOR_CLASS": Setting(
        package="spidermon",
        type=SettingType.OPT_OBJ,
        default_value=VersionedValue(None),
    ),
    "SPIDERMON_PERIODIC_MONITORS": Setting(
        package="spidermon",
        type=SettingType.DICT,
        default_value=VersionedValue({}),
        versioning=Versioning(added_in=Version("1.3.0")),
    ),
    "SPIDERMON_SPIDER_CLOSE_MONITORS": Setting(
        package="spidermon",
        type=SettingType.LIST,
        default_value=VersionedValue([]),
    ),
    "SPIDERMON_SPIDER_CLOSE_EXPRESSION_MONITORS": Setting(
        package="spidermon",
        type=SettingType.LIST,
        default_value=VersionedValue([]),
    ),
    "SPIDERMON_SPIDER_OPEN_MONITORS": Setting(
        package="spidermon",
        type=SettingType.LIST,
        default_value=VersionedValue([]),
    ),
    "SPIDERMON_SPIDER_OPEN_EXPRESSION_MONITORS": Setting(
        package="spidermon",
        type=SettingType.LIST,
        default_value=VersionedValue([]),
    ),
    "SPIDERMON_ENGINE_STOP_MONITORS": Setting(
        package="spidermon",
        type=SettingType.LIST,
        default_value=VersionedValue([]),
        versioning=Versioning(added_in=Version("1.9.0")),
    ),
    "SPIDERMON_ENGINE_STOP_EXPRESSION_MONITORS": Setting(
        package="spidermon",
        type=SettingType.LIST,
        default_value=VersionedValue([]),
        versioning=Versioning(added_in=Version("1.9.0")),
    ),
    "SPIDERMON_ADD_FIELD_COVERAGE": Setting(
        package="spidermon",
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
        versioning=Versioning(added_in=Version("1.14.0")),
    ),
    "SPIDERMON_FIELD_COVERAGE_SKIP_NONE": Setting(
        package="spidermon",
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
        versioning=Versioning(added_in=Version("1.14.0")),
    ),
    "SPIDERMON_FIELD_COVERAGE_SKIP_FALSY": Setting(
        package="spidermon",
        type=SettingType.BOOL,
        default_value=VersionedValue(True),
        versioning=Versioning(added_in=Version("1.27.0")),
    ),
    "SPIDERMON_FIELD_COVERAGE_SKIP_VALUES": Setting(
        package="spidermon",
        type=SettingType.LIST,
        default_value=VersionedValue(["", [], {}, "N/A", "-"]),
        versioning=Versioning(added_in=Version("1.27.0")),
    ),
    "SPIDERMON_LIST_FIELDS_COVERAGE_LEVELS": Setting(
        package="spidermon",
        type=SettingType.INT,
        default_value=VersionedValue(0),
        versioning=Versioning(added_in=Version("1.19.0")),
    ),
    "SPIDERMON_DICT_FIELDS_COVERAGE_LEVELS": Setting(package="spidermon"),
    "SPIDERMON_FIELD_COVERAGE_TOLERANCE": Setting(
        package="spidermon",
        type=SettingType.FLOAT,
        default_value=VersionedValue(0.0),
        versioning=Versioning(added_in=Version("1.26.0")),
    ),
    "SPIDERMON_MONITOR_SKIPPING_RULES": Setting(
        package="spidermon",
        type=SettingType.DICT,
        versioning=Versioning(added_in=Version("1.20.0")),
    ),
    # https://spidermon.readthedocs.io/en/latest/monitors.html
    "SPIDERMON_MAX_CRITICALS": Setting(
        package="spidermon",
        type=SettingType.INT,
        versioning=Versioning(added_in=Version("1.16.2")),
    ),
    "SPIDERMON_MAX_DOWNLOADER_EXCEPTIONS": Setting(
        package="spidermon",
        type=SettingType.INT,
        versioning=Versioning(added_in=Version("1.16.2")),
    ),
    "SPIDERMON_MAX_ERRORS": Setting(
        package="spidermon",
        type=SettingType.INT,
        versioning=Versioning(added_in=Version("1.9.0")),
    ),
    "SPIDERMON_FIELD_COVERAGE_SKIP_IF_NO_ITEM": Setting(
        package="spidermon",
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
        versioning=Versioning(added_in=Version("1.18.0")),
    ),
    "SPIDERMON_EXPECTED_FINISH_REASONS": Setting(
        package="spidermon",
        type=SettingType.LIST,
        default_value=VersionedValue(["finished"]),
        versioning=Versioning(added_in=Version("1.9.0")),
    ),
    "SPIDERMON_MIN_ITEMS": Setting(
        package="spidermon",
        type=SettingType.INT,
        versioning=Versioning(added_in=Version("1.9.0")),
    ),
    "SPIDERMON_MAX_ITEM_VALIDATION_ERRORS": Setting(
        package="spidermon",
        type=SettingType.INT,
        versioning=Versioning(added_in=Version("1.13.0")),
    ),
    "SPIDERMON_MAX_EXECUTION_TIME": Setting(
        package="spidermon",
        type=SettingType.INT,
        versioning=Versioning(added_in=Version("1.17.0")),
    ),
    "SPIDERMON_ITEM_COUNT_INCREASE": Setting(
        package="spidermon",
        type=SettingType.FLOAT,
        versioning=Versioning(added_in=Version("1.19.0")),
    ),
    "SPIDERMON_MAX_RETRIES": Setting(
        package="spidermon",
        type=SettingType.INT,
        default_value=VersionedValue(-1),
        versioning=Versioning(added_in=Version("1.16.2")),
    ),
    "SPIDERMON_MIN_SUCCESSFUL_REQUESTS": Setting(
        package="spidermon",
        type=SettingType.INT,
        default_value=VersionedValue(0),
        versioning=Versioning(added_in=Version("1.16.2")),
    ),
    "SPIDERMON_MAX_REQUESTS_ALLOWED": Setting(
        package="spidermon",
        type=SettingType.INT,
        default_value=VersionedValue(-1),
        versioning=Versioning(added_in=Version("1.16.2")),
    ),
    "SPIDERMON_UNWANTED_HTTP_CODES_MAX_COUNT": Setting(
        package="spidermon",
        type=SettingType.INT,
        default_value=VersionedValue(10),
        versioning=Versioning(added_in=Version("1.10.0")),
    ),
    "SPIDERMON_UNWANTED_HTTP_CODES": Setting(
        package="spidermon",
        type=SettingType.DICT_OR_LIST,
        default_value=VersionedValue(
            [400, 407, 429, 500, 502, 503, 504, 523, 540, 541],
        ),
        versioning=Versioning(added_in=Version("1.9.0")),
    ),
    "SPIDERMON_MAX_WARNINGS": Setting(
        package="spidermon",
        type=SettingType.INT,
        versioning=Versioning(added_in=Version("1.16.2")),
    ),
    "SPIDERMON_JOBS_COMPARISON": Setting(
        package="spidermon",
        type=SettingType.INT,
        default_value=VersionedValue(0),
        versioning=Versioning(added_in=Version("1.18.0")),
    ),
    "SPIDERMON_JOBS_COMPARISON_THRESHOLD": Setting(
        package="spidermon",
        type=SettingType.FLOAT,
        versioning=Versioning(added_in=Version("1.18.0")),
    ),
    "SPIDERMON_JOBS_COMPARISON_STATES": Setting(
        package="spidermon",
        type=SettingType.LIST,
        default_value=VersionedValue(["finished"]),
        versioning=Versioning(added_in=Version("1.18.0")),
    ),
    "SPIDERMON_JOBS_COMPARISON_TAGS": Setting(
        package="spidermon",
        type=SettingType.LIST,
        default_value=VersionedValue([]),
        versioning=Versioning(added_in=Version("1.18.0")),
    ),
    "SPIDERMON_JOBS_COMPARISON_CLOSE_REASONS": Setting(
        package="spidermon",
        type=SettingType.LIST,
        default_value=VersionedValue([]),
        versioning=Versioning(added_in=Version("1.23.0")),
    ),
    "SPIDERMON_JOBS_COMPARISON_ARGUMENTS": Setting(
        package="spidermon",
        type=SettingType.DICT,
        default_value=VersionedValue({}),
        versioning=Versioning(added_in=Version("1.24.0")),
    ),
    "SPIDERMON_JOBS_COMPARISON_ARGUMENTS_ENABLED": Setting(
        package="spidermon",
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
        versioning=Versioning(added_in=Version("1.24.0")),
    ),
    # https://spidermon.readthedocs.io/en/latest/item-validation.html
    "SPIDERMON_VALIDATION_ADD_ERRORS_TO_ITEMS": Setting(
        package="spidermon",
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
    ),
    "SPIDERMON_VALIDATION_DROP_ITEMS_WITH_ERRORS": Setting(
        package="spidermon",
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
    ),
    "SPIDERMON_VALIDATION_ERRORS_FIELD": Setting(
        package="spidermon",
        type=SettingType.STR,
        default_value=VersionedValue("_validation"),
    ),
    "SPIDERMON_VALIDATION_SCHEMAS": Setting(
        package="spidermon",
        type=SettingType.DICT_OR_LIST,
        default_value=VersionedValue([]),
    ),
    # https://spidermon.readthedocs.io/en/latest/howto/stats-collection.html
    "SPIDERMON_MAX_STORED_STATS": Setting(
        package="spidermon",
        type=SettingType.INT,
        default_value=VersionedValue(100),
        versioning=Versioning(added_in=Version("1.10.0")),
    ),
    # https://spidermon.readthedocs.io/en/latest/actions/email-action.html
    "SPIDERMON_EMAIL_SENDER": Setting(
        package="spidermon",
        type=SettingType.OPT_STR,
        default_value=VersionedValue(None),
    ),
    "SPIDERMON_EMAIL_TO": Setting(
        package="spidermon",
        type=SettingType.LIST,
        default_value=VersionedValue([]),
    ),
    "SPIDERMON_BODY_HTML": Setting(
        package="spidermon",
        type=SettingType.OPT_STR,
        default_value=VersionedValue(None),
    ),
    "SPIDERMON_BODY_HTML_TEMPLATE": Setting(
        package="spidermon",
        type=SettingType.STR,
        default_value=VersionedValue("reports/email/monitors/result.jinja"),
    ),
    "SPIDERMON_BODY_TEXT": Setting(
        package="spidermon",
        type=SettingType.OPT_STR,
        default_value=VersionedValue(None),
    ),
    "SPIDERMON_BODY_TEXT_TEMPLATE": Setting(
        package="spidermon",
        type=SettingType.OPT_STR,
        default_value=VersionedValue(None),
    ),
    "SPIDERMON_EMAIL_BCC": Setting(
        package="spidermon",
        type=SettingType.LIST,
        default_value=VersionedValue([]),
    ),
    "SPIDERMON_EMAIL_CONTEXT": Setting(
        package="spidermon",
        type=SettingType.DICT,
        default_value=VersionedValue({}),
    ),
    "SPIDERMON_EMAIL_CC": Setting(
        package="spidermon",
        type=SettingType.LIST,
        default_value=VersionedValue([]),
    ),
    "SPIDERMON_EMAIL_FAKE": Setting(
        package="spidermon",
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
    ),
    "SPIDERMON_EMAIL_REPLY_TO": Setting(
        package="spidermon",
        type=SettingType.OPT_STR,
        default_value=VersionedValue(None),
    ),
    "SPIDERMON_EMAIL_SUBJECT": Setting(
        package="spidermon",
        type=SettingType.OPT_STR,
        default_value=VersionedValue(None),
    ),
    "SPIDERMON_EMAIL_SUBJECT_TEMPLATE": Setting(
        package="spidermon",
        type=SettingType.OPT_STR,
        default_value=VersionedValue(None),
    ),
    "SPIDERMON_AWS_ACCESS_KEY": Setting(
        package="spidermon",
        type=SettingType.OPT_STR,
        default_value=VersionedValue(None),
        versioning=Versioning(deprecated_in=Version("1.12.0")),
        replacement="SPIDERMON_AWS_ACCESS_KEY_ID",
    ),
    "SPIDERMON_AWS_SECRET_KEY": Setting(
        package="spidermon",
        type=SettingType.OPT_STR,
        default_value=VersionedValue(None),
        is_secret=True,
        versioning=Versioning(deprecated_in=Version("1.12.0")),
        replacement="SPIDERMON_AWS_SECRET_ACCESS_KEY",
    ),
    "SPIDERMON_AWS_ACCESS_KEY_ID": Setting(
        package="spidermon",
        type=SettingType.OPT_STR,
        default_value=VersionedValue(None),
        versioning=Versioning(added_in=Version("1.12.0")),
    ),
    "SPIDERMON_AWS_SECRET_ACCESS_KEY": Setting(
        package="spidermon",
        type=SettingType.OPT_STR,
        default_value=VersionedValue(None),
        is_secret=True,
        versioning=Versioning(added_in=Version("1.12.0")),
    ),
    "SPIDERMON_AWS_REGION_NAME": Setting(
        package="spidermon",
        type=SettingType.OPT_STR,
        default_value=VersionedValue("us-east-1"),
    ),
    "SPIDERMON_AWS_RETURN_PATH": Setting(
        package="spidermon",
        type=SettingType.OPT_STR,
        default_value=VersionedValue(None),
        versioning=Versioning(added_in=Version("1.18.0")),
    ),
    "SPIDERMON_SMTP_HOST": Setting(
        package="spidermon",
        type=SettingType.OPT_STR,
        default_value=VersionedValue(None),
        versioning=Versioning(added_in=Version("1.17.0")),
    ),
    "SPIDERMON_SMTP_PORT": Setting(
        package="spidermon",
        type=SettingType.OPT_INT,
        default_value=VersionedValue(25),
        versioning=Versioning(added_in=Version("1.17.0")),
    ),
    "SPIDERMON_SMTP_USER": Setting(
        package="spidermon",
        type=SettingType.OPT_STR,
        default_value=VersionedValue(None),
        versioning=Versioning(added_in=Version("1.17.0")),
    ),
    "SPIDERMON_SMTP_PASSWORD": Setting(
        package="spidermon",
        type=SettingType.OPT_STR,
        default_value=VersionedValue(None),
        is_secret=True,
        versioning=Versioning(added_in=Version("1.17.0")),
    ),
    "SPIDERMON_SMTP_ENFORCE_TLS": Setting(
        package="spidermon",
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
        versioning=Versioning(added_in=Version("1.17.0")),
    ),
    "SPIDERMON_SMTP_ENFORCE_SSL": Setting(
        package="spidermon",
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
        versioning=Versioning(added_in=Version("1.17.0")),
    ),
    # https://spidermon.readthedocs.io/en/latest/actions/slack-action.html
    "SPIDERMON_SLACK_RECIPIENTS": Setting(
        package="spidermon",
        type=SettingType.LIST,
        default_value=VersionedValue([]),
    ),
    "SPIDERMON_SLACK_SENDER_NAME": Setting(
        package="spidermon",
        type=SettingType.STR,
    ),
    "SPIDERMON_SLACK_SENDER_TOKEN": Setting(
        package="spidermon",
        type=SettingType.STR,
        is_secret=True,
    ),
    "SPIDERMON_SLACK_ATTACHMENTS": Setting(
        package="spidermon",
        type=SettingType.OPT_STR,
        default_value=VersionedValue(None),
    ),
    "SPIDERMON_SLACK_ATTACHMENTS_TEMPLATE": Setting(
        package="spidermon",
        type=SettingType.OPT_STR,
        default_value=VersionedValue(None),
    ),
    "SPIDERMON_SLACK_FAKE": Setting(
        package="spidermon",
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
    ),
    "SPIDERMON_SLACK_INCLUDE_ATTACHMENTS": Setting(
        package="spidermon",
        type=SettingType.BOOL,
        default_value=VersionedValue(True),
    ),
    "SPIDERMON_SLACK_INCLUDE_MESSAGE": Setting(
        package="spidermon",
        type=SettingType.BOOL,
        default_value=VersionedValue(True),
    ),
    "SPIDERMON_SLACK_MESSAGE": Setting(
        package="spidermon",
        type=SettingType.OPT_STR,
        default_value=VersionedValue(None),
    ),
    "SPIDERMON_SLACK_MESSAGE_TEMPLATE": Setting(
        package="spidermon",
        type=SettingType.OPT_STR,
        default_value=VersionedValue(None),
    ),
    "SPIDERMON_SLACK_NOTIFIER_INCLUDE_ERROR_ATTACHMENTS": Setting(
        package="spidermon",
        type=SettingType.BOOL,
        default_value=VersionedValue(True),
    ),
    "SPIDERMON_SLACK_NOTIFIER_INCLUDE_OK_ATTACHMENTS": Setting(
        package="spidermon",
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
    ),
    "SPIDERMON_SLACK_NOTIFIER_INCLUDE_REPORT_LINK": Setting(
        package="spidermon",
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
    ),
    "SPIDERMON_SLACK_NOTIFIER_REPORT_INDEX": Setting(
        package="spidermon",
        type=SettingType.INT,
        default_value=VersionedValue(0),
    ),
    # https://spidermon.readthedocs.io/en/latest/actions/telegram-action.html
    "SPIDERMON_TELEGRAM_RECIPIENTS": Setting(
        package="spidermon",
        type=SettingType.LIST,
        default_value=VersionedValue([]),
        versioning=Versioning(added_in=Version("1.12.0")),
    ),
    "SPIDERMON_TELEGRAM_SENDER_TOKEN": Setting(
        package="spidermon",
        type=SettingType.STR,
        is_secret=True,
        versioning=Versioning(added_in=Version("1.12.0")),
    ),
    "SPIDERMON_TELEGRAM_FAKE": Setting(
        package="spidermon",
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
        versioning=Versioning(added_in=Version("1.12.0")),
    ),
    "SPIDERMON_TELEGRAM_MESSAGE": Setting(
        package="spidermon",
        type=SettingType.OPT_STR,
        default_value=VersionedValue(None),
        versioning=Versioning(added_in=Version("1.12.0")),
    ),
    "SPIDERMON_TELEGRAM_MESSAGE_TEMPLATE": Setting(
        package="spidermon",
        type=SettingType.OPT_STR,
        default_value=VersionedValue(None),
        versioning=Versioning(added_in=Version("1.12.0")),
    ),
    # https://spidermon.readthedocs.io/en/latest/actions/discord-action.html
    "SPIDERMON_DISCORD_WEBHOOK_URL": Setting(
        package="spidermon",
        type=SettingType.STR,
        is_secret=True,
        versioning=Versioning(added_in=Version("1.17.0")),
    ),
    "SPIDERMON_DISCORD_FAKE": Setting(
        package="spidermon",
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
        versioning=Versioning(added_in=Version("1.17.0")),
    ),
    "SPIDERMON_DISCORD_MESSAGE": Setting(
        package="spidermon",
        type=SettingType.OPT_STR,
        default_value=VersionedValue(None),
        versioning=Versioning(added_in=Version("1.17.0")),
    ),
    "SPIDERMON_DISCORD_MESSAGE_TEMPLATE": Setting(
        package="spidermon",
        type=SettingType.OPT_STR,
        default_value=VersionedValue(None),
        versioning=Versioning(added_in=Version("1.17.0")),
    ),
    # https://spidermon.readthedocs.io/en/latest/actions/job-tags-action.html
    "SPIDERMON_JOB_TAGS_TO_ADD": Setting(
        package="spidermon",
        type=SettingType.LIST,
        default_value=VersionedValue([]),
    ),
    "SPIDERMON_JOB_TAGS_TO_REMOVE": Setting(
        package="spidermon",
        type=SettingType.LIST,
        default_value=VersionedValue([]),
    ),
    # https://spidermon.readthedocs.io/en/latest/actions/file-report-action.html
    "SPIDERMON_REPORT_CONTEXT": Setting(
        package="spidermon",
        type=SettingType.DICT,
        default_value=VersionedValue({}),
    ),
    "SPIDERMON_REPORT_FILENAME": Setting(
        package="spidermon",
        type=SettingType.OPT_STR,
        default_value=VersionedValue(None),
    ),
    "SPIDERMON_REPORT_TEMPLATE": Setting(
        package="spidermon",
        type=SettingType.STR,
    ),
    "SPIDERMON_REPORT_S3_BUCKET": Setting(
        package="spidermon",
        type=SettingType.STR,
    ),
    "SPIDERMON_REPORT_S3_CONTENT_TYPE": Setting(
        package="spidermon",
        type=SettingType.OPT_STR,
        default_value=VersionedValue(None),
    ),
    "SPIDERMON_REPORT_S3_FILENAME": Setting(
        package="spidermon",
        type=SettingType.STR,
    ),
    "SPIDERMON_REPORT_S3_MAKE_PUBLIC": Setting(
        package="spidermon",
        type=SettingType.BOOL,
        default_value=VersionedValue(True),
    ),
    "SPIDERMON_REPORT_S3_REGION_ENDPOINT": Setting(
        package="spidermon",
        type=SettingType.OPT_STR,
        default_value=VersionedValue(None),
    ),
    # https://spidermon.readthedocs.io/en/latest/actions/sentry-action.html
    "SPIDERMON_SENTRY_DSN": Setting(
        package="spidermon",
        type=SettingType.STR,
        is_secret=True,
    ),
    "SPIDERMON_SENTRY_PROJECT_NAME": Setting(
        package="spidermon",
        type=SettingType.STR,
    ),
    "SPIDERMON_SENTRY_ENVIRONMENT_TYPE": Setting(
        package="spidermon",
        type=SettingType.OPT_STR,
        default_value=VersionedValue("Development"),
    ),
    "SPIDERMON_SENTRY_LOG_LEVEL": Setting(
        package="spidermon",
        type=SettingType.OPT_STR,
        default_value=VersionedValue("error"),
    ),
    "SPIDERMON_SENTRY_FAKE": Setting(
        package="spidermon",
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
    ),
    # https://spidermon.readthedocs.io/en/latest/actions/sns-action.html
    "SPIDERMON_SNS_TOPIC_ARN": Setting(
        package="spidermon",
        type=SettingType.STR,
        versioning=Versioning(added_in=Version("1.21.0")),
    ),
    # spidermon: undocumented settings
    "SPIDERMON_FIELD_COVERAGE_RULES": Setting(
        package="spidermon",
        type=SettingType.DICT,
        default_value=VersionedValue({}),
        versioning=Versioning(added_in=Version("1.14.0")),
    ),
    "SPIDERMON_TELEGRAM_NOTIFIER_INCLUDE_OK_MESSAGES": Setting(
        package="spidermon",
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
        versioning=Versioning(added_in=Version("1.12.0")),
    ),
    "SPIDERMON_TELEGRAM_NOTIFIER_INCLUDE_ERROR_MESSAGES": Setting(
        package="spidermon",
        type=SettingType.BOOL,
        default_value=VersionedValue(True),
        versioning=Versioning(added_in=Version("1.12.0")),
    ),
    "SPIDERMON_DISCORD_NOTIFIER_INCLUDE_OK_MESSAGES": Setting(
        package="spidermon",
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
        versioning=Versioning(added_in=Version("1.17.0")),
    ),
    "SPIDERMON_DISCORD_NOTIFIER_INCLUDE_ERROR_MESSAGES": Setting(
        package="spidermon",
        type=SettingType.BOOL,
        default_value=VersionedValue(True),
        versioning=Versioning(added_in=Version("1.17.0")),
    ),
    "SPIDERMON_VALIDATION_MODELS": Setting(
        package="spidermon",
        versioning=Versioning(
            removed_in=Version("1.19.0"),
            removal_guidance="use SPIDERMON_VALIDATION_SCHEMAS instead",
        ),
    ),
    # duplicate-url-discarder plugin settings, in order of appearance in
    # https://github.com/zytedata/duplicate-url-discarder#readme
    "DUD_FALLBACK_REQUEST_FINGERPRINTER_CLASS": Setting(
        package="duplicate-url-discarder",
        type=SettingType.OPT_OBJ,
        default_value=VersionedValue(None),
        versioning=Versioning(added_in=Version("0.1.0")),
    ),
    "DUD_LOAD_RULE_PATHS": Setting(
        package="duplicate-url-discarder",
        type=SettingType.LIST,
        default_value=VersionedValue([]),
        versioning=Versioning(added_in=Version("0.1.0")),
    ),
    "DUD_ATTRIBUTES_PER_ITEM": Setting(
        package="duplicate-url-discarder",
        type=SettingType.DICT,
        default_value=VersionedValue({}),
        versioning=Versioning(added_in=Version("0.2.0")),
    ),
    # zyte-common-items plugin settings, documented in
    # https://zyte-common-items.readthedocs.io/en/latest/reference/scrapy.html
    "ITEM_PROBABILITY_THRESHOLDS": Setting(
        package="zyte-common-items",
        type=SettingType.DICT,
        default_value=VersionedValue({"default": 0.1}),
        versioning=Versioning(added_in=Version("0.19.0")),
    ),
    # zyte-spider-templates plugin settings, in order of appearance in
    # https://zyte-spider-templates.readthedocs.io/en/latest/reference/settings.html
    "NAVIGATION_DEPTH_LIMIT": Setting(
        package="zyte-spider-templates",
        type=SettingType.INT,
        default_value=VersionedValue(0),
    ),
    "MAX_REQUESTS_PER_SEED": Setting(
        package="zyte-spider-templates",
        type=SettingType.INT,
        default_value=VersionedValue(0),
    ),
    "OFFSITE_REQUESTS_PER_SEED_ENABLED": Setting(
        package="zyte-spider-templates",
        type=SettingType.BOOL,
        default_value=VersionedValue(True),
    ),
    "ONLY_FEEDS_ENABLED": Setting(
        package="zyte-spider-templates",
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
    ),
    "INCREMENTAL_CRAWL_BATCH_SIZE": Setting(
        package="zyte-spider-templates",
        type=SettingType.INT,
        default_value=VersionedValue(50),
    ),
    "INCREMENTAL_CRAWL_COLLECTION_NAME": Setting(
        package="zyte-spider-templates",
        type=SettingType.OPT_STR,
    ),
    "INCREMENTAL_CRAWL_ENABLED": Setting(
        package="zyte-spider-templates",
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
    ),
    # scrapy-zyte-api plugin settings, in order of appearance in
    # https://scrapy-zyte-api.readthedocs.io/en/latest/reference/settings.html
    "ZYTE_API_AUTO_FIELD_STATS": Setting(
        package="scrapy-zyte-api",
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
        versioning=Versioning(added_in=Version("0.22.0")),
    ),
    "ZYTE_API_AUTOMAP_PARAMS": Setting(
        package="scrapy-zyte-api",
        type=SettingType.DICT,
        default_value=VersionedValue({}),
        versioning=Versioning(added_in=Version("0.6.0")),
    ),
    "ZYTE_API_BROWSER_HEADERS": Setting(
        package="scrapy-zyte-api",
        type=SettingType.DICT,
        default_value=VersionedValue({"Referer": "referer"}),
        versioning=Versioning(added_in=Version("0.6.0")),
    ),
    "ZYTE_API_COOKIE_MIDDLEWARE": Setting(
        package="scrapy-zyte-api",
        type=SettingType.OBJ,
        default_value=VersionedValue(
            "scrapy.downloadermiddlewares.cookies.CookiesMiddleware",
        ),
        versioning=Versioning(added_in=Version("0.8.0")),
    ),
    "ZYTE_API_DEFAULT_PARAMS": Setting(
        package="scrapy-zyte-api",
        type=SettingType.DICT,
        default_value=VersionedValue({}),
        versioning=Versioning(added_in=Version("0.2.0")),
    ),
    "ZYTE_API_ENABLED": Setting(
        package="scrapy-zyte-api",
        type=SettingType.BOOL,
        default_value=VersionedValue(True),
        versioning=Versioning(added_in=Version("0.6.0")),
    ),
    "ZYTE_API_ETH_KEY": Setting(
        package="scrapy-zyte-api",
        type=SettingType.OPT_STR,
        default_value=VersionedValue(None),
        is_secret=True,
        versioning=Versioning(added_in=Version("0.31.0")),
    ),
    "ZYTE_API_EXPERIMENTAL_COOKIES_ENABLED": Setting(
        package="scrapy-zyte-api",
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
        versioning=Versioning(added_in=Version("0.8.0")),
    ),
    "ZYTE_API_FALLBACK_HTTP_HANDLER": Setting(
        package="scrapy-zyte-api",
        type=SettingType.OBJ,
        # Default set as unknown because it depends on DOWNLOAD_HANDLERS.
        default_value=UNKNOWN_SETTING_VALUE,
        versioning=Versioning(added_in=Version("0.17.0")),
    ),
    "ZYTE_API_FALLBACK_HTTPS_HANDLER": Setting(
        package="scrapy-zyte-api",
        type=SettingType.OBJ,
        # Default set as unknown because it depends on DOWNLOAD_HANDLERS.
        default_value=UNKNOWN_SETTING_VALUE,
        versioning=Versioning(added_in=Version("0.17.0")),
    ),
    "ZYTE_API_FALLBACK_REQUEST_FINGERPRINTER_CLASS": Setting(
        package="scrapy-zyte-api",
        type=SettingType.OBJ,
        # Default set as unknown because it depends on whether scrapy-poet is
        # installed.
        default_value=UNKNOWN_SETTING_VALUE,
        versioning=Versioning(added_in=Version("0.7.0")),
    ),
    "ZYTE_API_KEY": Setting(
        package="scrapy-zyte-api",
        type=SettingType.OPT_STR,
        default_value=VersionedValue(None),
        is_secret=True,
        versioning=Versioning(added_in=Version("0.1.0")),
    ),
    "ZYTE_API_LOG_REQUESTS": Setting(
        package="scrapy-zyte-api",
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
        versioning=Versioning(added_in=Version("0.7.1")),
    ),
    "ZYTE_API_LOG_REQUESTS_TRUNCATE": Setting(
        package="scrapy-zyte-api",
        type=SettingType.INT,
        default_value=VersionedValue(64),
        versioning=Versioning(added_in=Version("0.7.1")),
    ),
    "ZYTE_API_MAX_COOKIE_BYTES": Setting(
        package="scrapy-zyte-api",
        type=SettingType.INT,
        default_value=VersionedValue(4097),
        versioning=Versioning(added_in=Version("0.35.0")),
    ),
    "ZYTE_API_MAX_COOKIE_NAME_LENGTH": Setting(
        package="scrapy-zyte-api",
        type=SettingType.INT,
        default_value=VersionedValue(4085),
        versioning=Versioning(added_in=Version("0.35.0")),
    ),
    "ZYTE_API_MAX_COOKIE_VALUE_LENGTH": Setting(
        package="scrapy-zyte-api",
        type=SettingType.INT,
        default_value=VersionedValue(4085),
        versioning=Versioning(added_in=Version("0.35.0")),
    ),
    "ZYTE_API_MAX_COOKIES": Setting(
        package="scrapy-zyte-api",
        type=SettingType.INT,
        default_value=VersionedValue(100),
        versioning=Versioning(added_in=Version("0.8.0")),
    ),
    "ZYTE_API_MAX_REQUESTS": Setting(
        package="scrapy-zyte-api",
        type=SettingType.OPT_INT,
        default_value=VersionedValue(None),
        versioning=Versioning(added_in=Version("0.11.0")),
    ),
    "ZYTE_API_PRESERVE_DELAY": Setting(
        package="scrapy-zyte-api",
        type=SettingType.BOOL,
        # Default set as unknown because it depends on AUTOTHROTTLE_ENABLED.
        default_value=UNKNOWN_SETTING_VALUE,
        versioning=Versioning(added_in=Version("0.20.0")),
    ),
    "ZYTE_API_PROVIDER_PARAMS": Setting(
        package="scrapy-zyte-api",
        type=SettingType.DICT,
        default_value=VersionedValue({}),
        versioning=Versioning(added_in=Version("0.12.0")),
    ),
    "ZYTE_API_REFERRER_POLICY": Setting(
        package="scrapy-zyte-api",
        type=SettingType.OBJ,
        default_value=VersionedValue("no-referrer"),
        versioning=Versioning(added_in=Version("0.26.0")),
    ),
    "ZYTE_API_RETRY_POLICY": Setting(
        package="scrapy-zyte-api",
        type=SettingType.IMPORT_PATH,
    ),
    "ZYTE_API_SESSION_CHECKER": Setting(
        package="scrapy-zyte-api",
        type=SettingType.OPT_OBJ,
        default_value=VersionedValue(None),
        versioning=Versioning(added_in=Version("0.19.0")),
    ),
    "ZYTE_API_SESSION_COOKIE_MODE": Setting(
        package="scrapy-zyte-api",
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
        versioning=Versioning(added_in=Version("0.35.0")),
    ),
    "ZYTE_API_SESSION_CREATION_RETRY_DELAY": Setting(
        package="scrapy-zyte-api",
        type=SettingType.FLOAT,
        default_value=VersionedValue(60.0),
        versioning=Versioning(added_in=Version("0.35.0")),
    ),
    "ZYTE_API_SESSION_DELAY": Setting(
        package="scrapy-zyte-api",
        type=SettingType.FLOAT,
        # Default set as unknown because it depends on DOWNLOAD_DELAY.
        default_value=UNKNOWN_SETTING_VALUE,
        versioning=Versioning(added_in=Version("0.33.0")),
    ),
    "ZYTE_API_SESSION_ENABLED": Setting(
        package="scrapy-zyte-api",
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
        versioning=Versioning(added_in=Version("0.19.0")),
    ),
    "ZYTE_API_SESSION_INIT_ACTION_FAILURE_INVALIDATES_SESSION": Setting(
        package="scrapy-zyte-api",
        type=SettingType.BOOL,
        default_value=VersionedValue(True),
        versioning=Versioning(added_in=Version("0.35.0")),
    ),
    "ZYTE_API_SESSION_LOCATION": Setting(
        package="scrapy-zyte-api",
        type=SettingType.DICT,
        default_value=VersionedValue({}),
        versioning=Versioning(added_in=Version("0.19.0")),
    ),
    "ZYTE_API_SESSION_MAX_BAD_INITS": Setting(
        package="scrapy-zyte-api",
        type=SettingType.INT,
        default_value=VersionedValue(8),
        versioning=Versioning(added_in=Version("0.19.0")),
    ),
    "ZYTE_API_SESSION_MAX_BAD_INITS_PER_POOL": Setting(
        package="scrapy-zyte-api",
        type=SettingType.DICT,
        default_value=VersionedValue({}),
        versioning=Versioning(added_in=Version("0.19.0")),
    ),
    "ZYTE_API_SESSION_MAX_CHECK_FAILURES": Setting(
        package="scrapy-zyte-api",
        type=SettingType.INT,
        default_value=VersionedValue(1),
        versioning=Versioning(added_in=Version("0.28.0")),
    ),
    "ZYTE_API_SESSION_MAX_ERRORS": Setting(
        package="scrapy-zyte-api",
        type=SettingType.INT,
        default_value=VersionedValue(1),
        versioning=Versioning(added_in=Version("0.19.0")),
    ),
    "ZYTE_API_SESSION_PARAMS": Setting(
        package="scrapy-zyte-api",
        type=SettingType.DICT,
        default_value=VersionedValue({}),
        versioning=Versioning(added_in=Version("0.19.0")),
    ),
    "ZYTE_API_SESSION_POOL_SIZE": Setting(
        package="scrapy-zyte-api",
        type=SettingType.INT,
    ),
    "ZYTE_API_SESSION_POOL_SIZES": Setting(
        package="scrapy-zyte-api",
        versioning=Versioning(
            added_in=Version("0.19.0"),
            deprecated_in=Version("0.33.0"),
            sunset_guidance=(
                'use ZYTE_API_SESSION_POOLS instead, with {pool: {"size": n}} values'
            ),
        ),
    ),
    "ZYTE_API_SESSION_POOLS": Setting(
        package="scrapy-zyte-api",
        type=SettingType.DICT,
    ),
    "ZYTE_API_SESSION_QUEUE_MAX_ATTEMPTS": Setting(
        package="scrapy-zyte-api",
        type=SettingType.INT,
        default_value=VersionedValue(60),
        versioning=Versioning(added_in=Version("0.19.0")),
    ),
    "ZYTE_API_SESSION_QUEUE_WAIT_TIME": Setting(
        package="scrapy-zyte-api",
        type=SettingType.FLOAT,
        default_value=VersionedValue(1.0),
        versioning=Versioning(added_in=Version("0.19.0")),
    ),
    "ZYTE_API_SESSION_RANDOMIZE_DELAY": Setting(
        package="scrapy-zyte-api",
        type=SettingType.BOOL,
        # Default set as unknown because it depends on RANDOMIZE_DOWNLOAD_DELAY.
        default_value=UNKNOWN_SETTING_VALUE,
        versioning=Versioning(added_in=Version("0.33.0")),
    ),
    "ZYTE_API_SESSION_RETRY_POLICY": Setting(
        package="scrapy-zyte-api",
        type=SettingType.IMPORT_PATH,
        versioning=Versioning(added_in=Version("0.35.0")),
    ),
    "ZYTE_API_SESSION_STATS_PER_POOL": Setting(
        package="scrapy-zyte-api",
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
        versioning=Versioning(added_in=Version("0.33.0")),
    ),
    "ZYTE_API_SKIP_HEADERS": Setting(
        package="scrapy-zyte-api",
        type=SettingType.LIST,
        default_value=VersionedValue(["Cookie"]),
        versioning=Versioning(added_in=Version("0.6.0")),
    ),
    "ZYTE_API_TRANSPARENT_MODE": Setting(
        package="scrapy-zyte-api",
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
        versioning=Versioning(added_in=Version("0.6.0")),
    ),
    "ZYTE_API_USE_ENV_PROXY": Setting(
        package="scrapy-zyte-api",
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
        versioning=Versioning(added_in=Version("0.10.0")),
    ),
    "ZYTE_API_WARN_ON_BAN_SENSITIVE_HEADERS": Setting(
        package="scrapy-zyte-api",
        type=SettingType.BOOL,
        default_value=VersionedValue(True),
        versioning=Versioning(added_in=Version("0.34.0")),
    ),
    # scrapy-zyte-api: undocumented settings
    "ZYTE_API_URL": Setting(
        package="scrapy-zyte-api",
        type=SettingType.OPT_STR,
        default_value=VersionedValue(None),
        versioning=Versioning(added_in=Version("0.3.0")),
    ),
    "_ZYTE_API_USER_AGENT": Setting(
        package="scrapy-zyte-api",
        type=SettingType.STR,
        # Default set as unknown because it depends on the installed versions
        # of scrapy-zyte-api and python-zyte-api.
        default_value=UNKNOWN_SETTING_VALUE,
        versioning=Versioning(added_in=Version("0.12.1")),
    ),
    # scrapy-zyte-smartproxy plugin settings, in order of appearance in
    # https://scrapy-zyte-smartproxy.readthedocs.io/en/latest/settings.html
    "ZYTE_SMARTPROXY_ENABLED": Setting(
        package="scrapy-zyte-smartproxy",
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
    ),
    "ZYTE_SMARTPROXY_APIKEY": Setting(
        package="scrapy-zyte-smartproxy",
        type=SettingType.OPT_STR,
        default_value=VersionedValue(None),
        is_secret=True,
    ),
    "ZYTE_SMARTPROXY_URL": Setting(
        package="scrapy-zyte-smartproxy",
        type=SettingType.STR,
        default_value=VersionedValue("http://proxy.zyte.com:8011"),
    ),
    "ZYTE_SMARTPROXY_MAXBANS": Setting(
        package="scrapy-zyte-smartproxy",
        type=SettingType.INT,
        default_value=VersionedValue(400),
    ),
    "ZYTE_SMARTPROXY_DOWNLOAD_TIMEOUT": Setting(
        package="scrapy-zyte-smartproxy",
        type=SettingType.INT,
        default_value=VersionedValue(190),
    ),
    "ZYTE_SMARTPROXY_PRESERVE_DELAY": Setting(
        package="scrapy-zyte-smartproxy",
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
    ),
    "ZYTE_SMARTPROXY_DEFAULT_HEADERS": Setting(
        package="scrapy-zyte-smartproxy",
        type=SettingType.DICT,
        default_value=VersionedValue({}),
    ),
    "ZYTE_SMARTPROXY_BACKOFF_STEP": Setting(
        package="scrapy-zyte-smartproxy",
        type=SettingType.INT,
        default_value=VersionedValue(15),
    ),
    "ZYTE_SMARTPROXY_BACKOFF_MAX": Setting(
        package="scrapy-zyte-smartproxy",
        type=SettingType.INT,
        default_value=VersionedValue(180),
    ),
    "ZYTE_SMARTPROXY_FORCE_ENABLE_ON_HTTP_CODES": Setting(
        package="scrapy-zyte-smartproxy",
        type=SettingType.LIST,
        default_value=VersionedValue([]),
    ),
    "ZYTE_SMARTPROXY_KEEP_HEADERS": Setting(
        package="scrapy-zyte-smartproxy",
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
        versioning=Versioning(added_in=Version("2.4.0")),
    ),
    # scrapy-zyte-smartproxy plugin settings deprecated in favor of the
    # ZYTE_SMARTPROXY_* ones above, still read with a ScrapyDeprecationWarning.
    "HUBPROXY_ENABLED": Setting(
        package="scrapy-zyte-smartproxy",
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
        versioning=Versioning(deprecated_in=UNKNOWN_UNSUPPORTED_VERSION),
        replacement="ZYTE_SMARTPROXY_ENABLED",
    ),
    "HUBPROXY_APIKEY": Setting(
        package="scrapy-zyte-smartproxy",
        type=SettingType.OPT_STR,
        default_value=VersionedValue(None),
        is_secret=True,
        versioning=Versioning(deprecated_in=UNKNOWN_UNSUPPORTED_VERSION),
        replacement="ZYTE_SMARTPROXY_APIKEY",
    ),
    "HUBPROXY_URL": Setting(
        package="scrapy-zyte-smartproxy",
        type=SettingType.STR,
        default_value=VersionedValue("http://proxy.zyte.com:8011"),
        versioning=Versioning(deprecated_in=UNKNOWN_UNSUPPORTED_VERSION),
        replacement="ZYTE_SMARTPROXY_URL",
    ),
    "HUBPROXY_MAXBANS": Setting(
        package="scrapy-zyte-smartproxy",
        type=SettingType.INT,
        default_value=VersionedValue(400),
        versioning=Versioning(deprecated_in=UNKNOWN_UNSUPPORTED_VERSION),
        replacement="ZYTE_SMARTPROXY_MAXBANS",
    ),
    "HUBPROXY_DOWNLOAD_TIMEOUT": Setting(
        package="scrapy-zyte-smartproxy",
        type=SettingType.INT,
        default_value=VersionedValue(190),
        versioning=Versioning(deprecated_in=UNKNOWN_UNSUPPORTED_VERSION),
        replacement="ZYTE_SMARTPROXY_DOWNLOAD_TIMEOUT",
    ),
    "HUBPROXY_PRESERVE_DELAY": Setting(
        package="scrapy-zyte-smartproxy",
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
        versioning=Versioning(deprecated_in=UNKNOWN_UNSUPPORTED_VERSION),
        replacement="ZYTE_SMARTPROXY_PRESERVE_DELAY",
    ),
    "HUBPROXY_BACKOFF_STEP": Setting(
        package="scrapy-zyte-smartproxy",
        type=SettingType.INT,
        default_value=VersionedValue(15),
        versioning=Versioning(deprecated_in=UNKNOWN_UNSUPPORTED_VERSION),
        replacement="ZYTE_SMARTPROXY_BACKOFF_STEP",
    ),
    "HUBPROXY_BACKOFF_MAX": Setting(
        package="scrapy-zyte-smartproxy",
        type=SettingType.INT,
        default_value=VersionedValue(180),
        versioning=Versioning(deprecated_in=UNKNOWN_UNSUPPORTED_VERSION),
        replacement="ZYTE_SMARTPROXY_BACKOFF_MAX",
    ),
    "HUBPROXY_FORCE_ENABLE_ON_HTTP_CODES": Setting(
        package="scrapy-zyte-smartproxy",
        type=SettingType.LIST,
        default_value=VersionedValue([]),
        versioning=Versioning(deprecated_in=UNKNOWN_UNSUPPORTED_VERSION),
        replacement="ZYTE_SMARTPROXY_FORCE_ENABLE_ON_HTTP_CODES",
    ),
    # scrapy-crawlera settings, from before the package was renamed
    # scrapy-zyte-smartproxy, no longer read at all as of that rename.
    "CRAWLERA_ENABLED": Setting(
        package="scrapy-zyte-smartproxy",
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
        versioning=Versioning(
            removed_in=Version("2.0.0"),
            removal_guidance="use ZYTE_SMARTPROXY_ENABLED instead",
        ),
    ),
    "CRAWLERA_APIKEY": Setting(
        package="scrapy-zyte-smartproxy",
        type=SettingType.OPT_STR,
        default_value=VersionedValue(None),
        is_secret=True,
        versioning=Versioning(
            removed_in=Version("2.0.0"),
            removal_guidance="use ZYTE_SMARTPROXY_APIKEY instead",
        ),
    ),
    "CRAWLERA_URL": Setting(
        package="scrapy-zyte-smartproxy",
        type=SettingType.STR,
        default_value=VersionedValue("http://proxy.zyte.com:8011"),
        versioning=Versioning(
            removed_in=Version("2.0.0"),
            removal_guidance="use ZYTE_SMARTPROXY_URL instead",
        ),
    ),
    "CRAWLERA_MAXBANS": Setting(
        package="scrapy-zyte-smartproxy",
        type=SettingType.INT,
        default_value=VersionedValue(400),
        versioning=Versioning(
            removed_in=Version("2.0.0"),
            removal_guidance="use ZYTE_SMARTPROXY_MAXBANS instead",
        ),
    ),
    "CRAWLERA_DOWNLOAD_TIMEOUT": Setting(
        package="scrapy-zyte-smartproxy",
        type=SettingType.INT,
        default_value=VersionedValue(190),
        versioning=Versioning(
            removed_in=Version("2.0.0"),
            removal_guidance="use ZYTE_SMARTPROXY_DOWNLOAD_TIMEOUT instead",
        ),
    ),
    "CRAWLERA_PRESERVE_DELAY": Setting(
        package="scrapy-zyte-smartproxy",
        type=SettingType.BOOL,
        default_value=VersionedValue(False),
        versioning=Versioning(
            removed_in=Version("2.0.0"),
            removal_guidance="use ZYTE_SMARTPROXY_PRESERVE_DELAY instead",
        ),
    ),
    "CRAWLERA_DEFAULT_HEADERS": Setting(
        package="scrapy-zyte-smartproxy",
        type=SettingType.DICT,
        default_value=VersionedValue({}),
        versioning=Versioning(
            removed_in=Version("2.0.0"),
            removal_guidance="use ZYTE_SMARTPROXY_DEFAULT_HEADERS instead",
        ),
    ),
    "CRAWLERA_BACKOFF_STEP": Setting(
        package="scrapy-zyte-smartproxy",
        type=SettingType.INT,
        default_value=VersionedValue(15),
        versioning=Versioning(
            removed_in=Version("2.0.0"),
            removal_guidance="use ZYTE_SMARTPROXY_BACKOFF_STEP instead",
        ),
    ),
    "CRAWLERA_BACKOFF_MAX": Setting(
        package="scrapy-zyte-smartproxy",
        type=SettingType.INT,
        default_value=VersionedValue(180),
        versioning=Versioning(
            removed_in=Version("2.0.0"),
            removal_guidance="use ZYTE_SMARTPROXY_BACKOFF_MAX instead",
        ),
    ),
    "CRAWLERA_FORCE_ENABLE_ON_HTTP_CODES": Setting(
        package="scrapy-zyte-smartproxy",
        type=SettingType.LIST,
        default_value=VersionedValue([]),
        versioning=Versioning(
            removed_in=Version("2.0.0"),
            removal_guidance="use ZYTE_SMARTPROXY_FORCE_ENABLE_ON_HTTP_CODES instead",
        ),
    ),
    # Removed even earlier, from the still-named-scrapy-crawlera package,
    # collapsed into a single API key instead of a username and a password.
    "CRAWLERA_USER": Setting(
        package="scrapy-zyte-smartproxy",
        is_secret=True,
        versioning=Versioning(
            removed_in=Version("1.5.1"),
            removal_guidance="use ZYTE_SMARTPROXY_APIKEY instead",
        ),
    ),
    "CRAWLERA_PASS": Setting(
        package="scrapy-zyte-smartproxy",
        is_secret=True,
        versioning=Versioning(
            removed_in=Version("1.5.1"),
            removal_guidance="use ZYTE_SMARTPROXY_APIKEY instead",
        ),
    ),
}

for name, setting in SETTINGS.items():
    setting.name = name
