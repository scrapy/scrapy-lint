from __future__ import annotations

from tests.helpers import check_project
from tests.settings import SETTING_VALUE_CHECK_TEMPLATES, SafeDict, zip_with_template

from . import NO_ISSUE, Cases, ExpectedIssue, File, cases

CASES: Cases = (
    # Python file checks
    *(
        (
            [File(code, path=path)],
            issues,
            {},
        )
        for path in ["a.py"]
        for code, issues in (
            # Setting value checks
            *(
                (
                    template.format_map(SafeDict(setting=setting, value=value)),
                    NO_ISSUE,
                )
                for template, setting, value in zip_with_template(
                    (
                        *(
                            (template,)
                            for template, _, _ in SETTING_VALUE_CHECK_TEMPLATES
                        ),
                    ),
                    (
                        # SCP36 invalid setting value (valid values)
                        ("AWS_ACCESS_KEY_ID", "foo"),
                        ("AWS_ACCESS_KEY_ID", "foo()"),
                        ("AWS_ACCESS_KEY_ID", '"AKIAIOSFODNN7EXAMPLE"'),
                        ("AWS_ACCESS_KEY_ID", "None"),
                        ("BOT_NAME", "foo"),
                        ("BOT_NAME", "foo()"),
                        ("BOT_NAME", '"mybot"'),
                        ("BOT_NAME", '"mybot"'),
                        ("CONCURRENT_REQUESTS", "foo"),
                        ("CONCURRENT_REQUESTS", "foo()"),
                        ("CONCURRENT_REQUESTS", '"1"'),
                        ("CONCURRENT_REQUESTS", 'b"1"'),
                        ("CONCURRENT_REQUESTS", "1.0"),
                        ("CONCURRENT_REQUESTS", "1"),
                        ("CONCURRENT_REQUESTS", "True"),
                        ("DEFAULT_ITEM_CLASS", "foo"),
                        ("DEFAULT_ITEM_CLASS", "foo()"),
                        ("DEFAULT_ITEM_CLASS", "MyItem"),
                        ("DEFAULT_REQUEST_HEADERS", "foo"),
                        ("DEFAULT_REQUEST_HEADERS", "foo()"),
                        ("DEFAULT_REQUEST_HEADERS", "None"),
                        ("DEFAULT_REQUEST_HEADERS", "{}"),
                        ("DEFAULT_REQUEST_HEADERS", "'{}'"),
                        ("DEFAULT_REQUEST_HEADERS", "{a: b}"),
                        ("DEFAULT_REQUEST_HEADERS", "[(a, b)]"),
                        ("DEFAULT_REQUEST_HEADERS", '\'[["a", "b"]]\''),
                        ("DEFAULT_REQUEST_HEADERS", "{'Foo': 'Bar'}"),
                        (
                            "DEFAULT_REQUEST_HEADERS",
                            "{1: 'keys do not have to be str'}",
                        ),
                        ("DOWNLOAD_BIND_ADDRESS", "foo"),
                        ("DOWNLOAD_BIND_ADDRESS", "None"),
                        ("DOWNLOAD_BIND_ADDRESS", '"127.0.0.2"'),
                        ("DOWNLOAD_BIND_ADDRESS", '("127.0.0.2", 5000)'),
                        ("DOWNLOAD_BIND_ADDRESS", "(host, port)"),
                        ("DOWNLOAD_HANDLERS", "foo"),
                        ("DOWNLOAD_HANDLERS", "foo()"),
                        ("DOWNLOAD_HANDLERS", "None"),
                        ("DOWNLOAD_HANDLERS", "{}"),
                        ("DOWNLOAD_HANDLERS", "'{}'"),
                        ("DOWNLOAD_HANDLERS", "{a: b}"),
                        ("DOWNLOAD_HANDLERS", "{'http': None}"),
                        ("DOWNLOAD_HANDLERS", "{'websocket': WebSocketHandler}"),
                        ("DOWNLOAD_HANDLERS", "dict(http=None)"),
                        ("DOWNLOAD_HANDLERS", "dict(websocket=WebSocketHandler)"),
                        ("DOWNLOAD_SLOTS", "foo"),
                        ("DOWNLOAD_SLOTS", "foo()"),
                        ("DOWNLOAD_SLOTS", '"{}"'),
                        ("DOWNLOAD_SLOTS", "{a: b}"),
                        ("DOWNLOAD_SLOTS", "{a: {b: c}}"),
                        ("DOWNLOAD_SLOTS", '{"toscrape.com": {"concurrency": 1}}'),
                        ("DOWNLOAD_SLOTS", '{"toscrape.com": {"delay": 0.0}}'),
                        ("DOWNLOAD_SLOTS", '{"toscrape.com": {"jitter": 0.5}}'),
                        (
                            "DOWNLOAD_SLOTS",
                            '{"toscrape.com": {"randomize_delay": True}}',
                        ),
                        ("DOWNLOAD_SLOTS", '{"toscrape.com": {}}'),
                        ("DOWNLOAD_SLOTS", '\'{"toscrape.com": {"concurrency": 1}}\''),
                        ("DOWNLOAD_SLOTS", "{}"),
                        ("DOWNLOAD_SLOTS", "[]"),
                        ("DOWNLOAD_SLOTS", '"[]"'),
                        ("DOWNLOAD_SLOTS", "None"),
                        ("DOWNLOADER_CLIENT_TLS_METHOD", "foo"),
                        ("DOWNLOADER_CLIENT_TLS_METHOD", "foo()"),
                        ("DOWNLOADER_CLIENT_TLS_METHOD", '"TLS"'),
                        ("DOWNLOADER_CLIENT_TLS_METHOD", '"TLSv1.2"'),
                        ("DOWNLOADER_MIDDLEWARES", "foo"),
                        ("DOWNLOADER_MIDDLEWARES", "foo()"),
                        ("DOWNLOADER_MIDDLEWARES", "{}"),
                        ("DOWNLOADER_MIDDLEWARES", "'{}'"),
                        ("DOWNLOADER_MIDDLEWARES", "{a: b}"),
                        ("DOWNLOADER_MIDDLEWARES", "{Foo: 100}"),
                        ("DOWNLOADER_MIDDLEWARES", "{'foo.Foo': 100}"),
                        # SCP60 unsorted priority dict (sorted values)
                        ("DOWNLOADER_MIDDLEWARES", "{Foo: 100, Bar: 200}"),
                        # Disabled components have no priority to sort by.
                        ("DOWNLOADER_MIDDLEWARES", "{Foo: None, Bar: 100}"),
                        # Entries with the same priority can come in any order.
                        ("DOWNLOADER_MIDDLEWARES", "{Foo: 200, Bar: 200}"),
                        # Priorities that are not literals cannot be sorted.
                        ("DOWNLOADER_MIDDLEWARES", "{Foo: 200, Bar: prio}"),
                        ("DOWNLOADER_MIDDLEWARES", "{**BASE, Foo: 100}"),
                        ("FEED_EXPORT_FIELDS", "foo"),
                        ("FEED_EXPORT_FIELDS", "foo()"),
                        ("FEED_EXPORT_FIELDS", '"foo"'),
                        ("FEED_EXPORT_FIELDS", "()"),
                        ("FEED_EXPORT_FIELDS", "[]"),
                        ("FEED_EXPORT_FIELDS", "{}"),
                        ("FEED_EXPORT_FIELDS", "None"),
                        ("FEED_EXPORT_INDENT", '"2"'),
                        ("FEED_EXPORT_INDENT", "0"),
                        ("FEED_EXPORT_INDENT", "1"),
                        ("FEED_EXPORT_INDENT", "None"),
                        ("FEED_EXPORT_INDENT", "True"),
                        ("FEED_URI", "foo"),
                        ("FEED_URI", "foo()"),
                        ("FEED_URI", "Path(foo)"),
                        ("FEED_URI", "Path(foo())"),
                        ("FEED_URI", "Path()"),  # Bad, but not Scrapy-specific
                        ("FEED_URI", "Path(1)"),  # Bad, but not Scrapy-specific
                        ("FEED_URI_PARAMS", "foo"),
                        ("FEED_URI_PARAMS", "foo()"),
                        ("FEED_URI_PARAMS", '"myproject.utils.get_uri_params"'),
                        ("FEED_URI_PARAMS", "None"),
                        ("FEED_URI_PARAMS", "uri_params"),
                        ("FEED_URI_PARAMS", "my_project.feeds.uri_params"),
                        ("FEEDS", "foo"),
                        ("FEEDS", "foo()"),
                        ("FEEDS", '"{}"'),
                        ("FEEDS", "[]"),
                        ("FEEDS", '"[]"'),
                        ("FEEDS", "None"),
                        (
                            "FEEDS",
                            '{f: {"format": "csv", "fields": ["name", "price"], "encoding": "utf-8"}}',
                        ),
                        (
                            "FEEDS",
                            '{f: {"format": "json", "batch_item_count": 0, "indent": 0, "fields": None}}',
                        ),
                        (
                            "FEEDS",
                            '{f: {"format": "json", "batch_item_count": 0, "indent": 0, "fields": foo}}',
                        ),
                        ("FEEDS", '{f: {"format": "json"}}'),
                        (
                            "FEEDS",
                            '{f:{"item_classes":[ProductItem],"item_filter":MyFilter,"uri_params":get_uri_params,}}',
                        ),
                        ("FEEDS", '{f: {"item_export_kwargs": kwargs}}'),
                        ("FEEDS", '{f: {"fields": field_list}}'),
                        (
                            "FEEDS",
                            '{f: {"format": "xml", "batch_item_count": 100, "encoding": None, "fields": {"name": "product_name", "price": "product_price"}, "item_classes": ["myproject.items.ProductItem"], "item_filter": "myproject.filters.MyFilter", "indent": 2, "item_export_kwargs": {"root_element": "products"}, "overwrite": True, "store_empty": False, "uri_params": "myproject.utils.get_uri_params"}}',
                        ),
                        ("FEEDS", '\'{"output.json": {"format": "json"}}\''),
                        ("FEEDS", "{}"),
                        ("FEEDS", "{a: b}"),
                        ("FEEDS", "{a: {b: c}}"),
                        ("FEEDS", '{"ftp://user:p%40ss@example.com:21/f.json": {}}'),
                        ("FEEDS", '{"ftp://[::1]:21/f.json": {}}'),
                        # A URI param can also stand for the port.
                        ("FEEDS", '{"ftp://example.com:%(port)s/f.json": {}}'),
                        # Outside the authority, "@" is part of the path.
                        ("FEEDS", '{"s3://bucket/jane.doe@example.com.csv": {}}'),
                        ("FEED_URI", '"ftp://user:p%40ss@example.com/f.json"'),
                        ("JOBDIR", "foo"),
                        ("JOBDIR", "foo()"),
                        ("JOBDIR", '"/tmp/foo"'),
                        ("JOBDIR", 'Path("/tmp/foo")'),
                        ("JOBDIR", "None"),
                        ("LOG_LEVEL", "foo"),
                        ("LOG_LEVEL", "foo()"),
                        ("LOG_LEVEL", '"debug"'),
                        ("LOG_LEVEL", '"INFO"'),
                        ("LOG_LEVEL", "0"),
                        ("LOG_LEVEL", "20"),
                        ("LOG_LEVEL", "25"),
                        ("LOG_VERSIONS", "foo"),
                        ("LOG_VERSIONS", "foo()"),
                        ("LOG_VERSIONS", '"foo,bar"'),
                        ("LOG_VERSIONS", '"foo"'),
                        ("LOG_VERSIONS", '["foo", "bar"]'),
                        ("LOG_VERSIONS", '["foo"]'),
                        ("LOG_VERSIONS", "b''"),
                        ("LOG_VERSIONS", "()"),
                        ("LOG_VERSIONS", "[]"),
                        ("LOG_VERSIONS", "{}"),
                        ("LOG_VERSIONS", "range(2)"),
                        ("LOG_VERSIONS", "set()"),
                        ("LOG_VERSIONS", "None"),
                        ("LOGSTATS_INTERVAL", "foo"),
                        ("LOGSTATS_INTERVAL", "foo()"),
                        ("LOGSTATS_INTERVAL", '"1.0"'),
                        ("LOGSTATS_INTERVAL", 'b"1.0"'),
                        ("LOGSTATS_INTERVAL", "1.0"),
                        ("LOGSTATS_INTERVAL", "1"),
                        ("LOGSTATS_INTERVAL", "True"),
                        ("PERIODIC_LOG_DELTA", "foo"),
                        ("PERIODIC_LOG_DELTA", "foo()"),
                        ("PERIODIC_LOG_DELTA", "None"),
                        ("PERIODIC_LOG_DELTA", "True"),
                        ("PERIODIC_LOG_DELTA", "{}"),
                        ("PERIODIC_LOG_DELTA", "{a: [b, c]}"),
                        ("PERIODIC_LOG_DELTA", '{"exclude": foo}'),
                        (
                            "PERIODIC_LOG_DELTA",
                            '{"exclude": ["downloader/response_count"]}',
                        ),
                        ("PERIODIC_LOG_DELTA", '{"exclude": []}'),
                        (
                            "PERIODIC_LOG_DELTA",
                            '{"include": ["stats"], "exclude": ["other"]}',
                        ),
                        ("PERIODIC_LOG_DELTA", '{"include": ["stats"]}'),
                        ("PERIODIC_LOG_DELTA", '{"include": []}'),
                        ("SCHEDULER", "foo"),
                        ("SCHEDULER", "foo()"),
                        ("SCHEDULER", "CustomScheduler"),
                        ("SCHEDULER", "my_project.schedulers.CustomScheduler"),
                        ("SPIDER_CONTRACTS", "foo"),
                        ("SPIDER_CONTRACTS", "foo()"),
                        ("SPIDER_CONTRACTS", '"{}"'),
                        ("SPIDER_CONTRACTS", "{}"),
                        ("SPIDER_CONTRACTS", "None"),
                        ("ZYTE_API_RETRY_POLICY", '"zyte_api.aggressive_retrying"'),
                        ("ZYTE_API_RETRY_POLICY", "foo"),
                        ("ZYTE_API_RETRY_POLICY", "foo()"),
                        (
                            "ZYTE_API_SESSION_RETRY_POLICY",
                            '"scrapy_zyte_api.SESSION_AGGRESSIVE_RETRY_POLICY"',
                        ),
                        ("ZYTE_API_KEY", "foo"),
                        ("ZYTE_API_KEY", "foo()"),
                        ("ZYTE_API_KEY", 'os.environ["ZYTE_API_KEY"]'),
                        # Unknown setting type
                        ("SERVICE_ROOT", "foo"),
                        ("SERVICE_ROOT", "foo()"),
                        # SCP37 unpicklable setting value (valid values)
                        ("LOG_VERSIONS", "list((k for k in deps))"),
                        # SCP39 no contact info (valid values)
                        *(
                            ("USER_AGENT", value)
                            for value in (
                                "foo",
                                "foo()",
                                '"https://jane.doe.example"',
                                '"Jane Doe (https://jane.doe.example)"',
                                '"Jane Doe (+https://jane.doe.example)"',
                                '"jane.doe@example.com"',
                                '"Jane Doe (jane.doe@example.com)"',
                                '"Jane Doe (+mailto:jane.doe@example.com)"',
                                '"+1 555-9292"',
                                '"Jane Doe (+1 (555) 92.92))"',
                                '"Jane Doe (+tel:+15559292"',
                            )
                        ),
                        # SCP42 unneeded path string (valid values)
                        #
                        # FEED_URI supports Path since Scrapy 2.0.0+.
                        ("FEED_URI", 'Path("output.jsonl")'),
                        # URI params require a string, though:
                        # https://github.com/scrapy/scrapy/issues/6425
                        ("FEED_URI", '"output-%(time)s.jsonl"'),
                        ("FEED_URI", '"file:///home/user/output-%(time)s.jsonl"'),
                        # The value of LOG_FILE is directly passed to the
                        # Python API, and should support Path objects on Python
                        # 3.6+.
                        ("LOG_FILE", 'Path("scrapy.log")'),
                        # FEED_URI and LOG_FILE can be None
                        ("FEED_URI", "None"),
                        ("LOG_FILE", "None"),
                        # SCP53 hardcoded secret (valid values)
                        (
                            "AWS_SECRET_ACCESS_KEY",
                            "os.environ['AWS_SECRET_ACCESS_KEY']",
                        ),
                        ("AWS_SECRET_ACCESS_KEY", "None"),
                        # An empty value disables the credential:
                        ("MAIL_PASS", '""'),
                        # The default value is public knowledge:
                        ("FTP_PASSWORD", '"guest"'),
                    ),
                )
            ),
        )
    ),
)


@cases(CASES)
def test(
    files: File | list[File],
    expected: ExpectedIssue | list[ExpectedIssue] | None,
    options,
):
    check_project(files, expected, options)
