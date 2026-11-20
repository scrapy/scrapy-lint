from __future__ import annotations

from tests.helpers import check_project

from . import (
    NO_ISSUE,
    Cases,
    ExpectedIssue,
    File,
    cases,
    insecure_scrapy_issues,
    iter_issues,
    outdated_scrapy,
)
from .test_settings import SETTING_VALUE_CHECK_TEMPLATES, SafeDict, zip_with_template

CASES: Cases = (
    # Checks bassed on requirements and setting values
    *(
        (
            (
                File("", path="scrapy.cfg"),
                File(requirements, path="requirements.txt"),
                File(f"settings[{name!r}] = {value}", path=path),
            ),
            (
                ExpectedIssue(
                    "SCP13 incomplete requirements freeze",
                    path="requirements.txt",
                ),
                *insecure_scrapy_issues(requirements),
                *outdated_scrapy(requirements),
                *iter_issues(issues),
            ),
            {},
        )
        for path in ("a.py",)
        for requirements, name, value, issues in (
            # SCP36 invalid setting value: FEEDS keys
            *(
                (
                    f"scrapy=={version}",
                    "FEEDS",
                    value,
                    (
                        *(
                            ExpectedIssue(
                                f"SCP29 setting needs upgrade: {key!r} "
                                f"requires Scrapy {versions[1]}+",
                                column=25,
                                path=path,
                            )
                            for _ in range(1)
                            if has_issue
                        ),
                    ),
                )
                for key, versions, value in (
                    (
                        "batch_item_count",
                        ("2.2.0", "2.3.0"),
                        '{f: {"batch_item_count": 100}}',
                    ),
                    (
                        "item_export_kwargs",
                        ("2.3.0", "2.4.0"),
                        '{f: {"item_export_kwargs": {}}}',
                    ),
                    ("overwrite", ("2.3.0", "2.4.0"), '{f: {"overwrite": False}}'),
                    (
                        "item_classes",
                        ("2.5.0", "2.6.0"),
                        '{f: {"item_classes": [MyItem]}}',
                    ),
                    (
                        "item_filter",
                        ("2.5.0", "2.6.0"),
                        '{f: {"item_filter": MyFilter}}',
                    ),
                    (
                        "postprocessing",
                        ("2.5.0", "2.6.0"),
                        '{f: {"postprocessing": []}}',
                    ),
                )
                for version, has_issue in zip(versions, (True, False), strict=False)
            ),
            # SCP29 setting needs upgrade, SCP36 invalid setting value:
            # DOWNLOAD_SLOTS keys
            *(
                (f"scrapy=={version}", "DOWNLOAD_SLOTS", value, issues)
                for version, value, issues in (
                    (
                        "2.18.0",
                        '{f: {"jitter": 0}}',
                        ExpectedIssue(
                            "SCP29 setting needs upgrade: 'jitter' requires "
                            "Scrapy 2.19.0+",
                            column=34,
                            path=path,
                        ),
                    ),
                    ("2.19.0", '{f: {"jitter": 0}}', NO_ISSUE),
                    ("2.18.0", '{f: {"randomize_delay": True}}', NO_ISSUE),
                    (
                        "2.19.0",
                        '{f: {"randomize_delay": True}}',
                        ExpectedIssue(
                            "SCP36 invalid setting value: randomize_delay is "
                            "deprecated in scrapy 2.19.0; use jitter instead",
                            column=34,
                            path=path,
                        ),
                    ),
                )
            ),
        )
    ),
    *(
        (
            [
                File("", path="scrapy.cfg"),
                File(requirements, path="requirements.txt"),
                File(code, path=path),
            ],
            (
                ExpectedIssue(
                    "SCP13 incomplete requirements freeze",
                    path="requirements.txt",
                ),
                *insecure_scrapy_issues(requirements),
                *outdated_scrapy(requirements),
                *iter_issues(issues),
            ),
            {},
        )
        for path in ["a.py"]
        for requirements, code, issues in (
            *(
                (
                    requirements,
                    template.format_map(SafeDict(setting=setting, value=value)),
                    ExpectedIssue(
                        issue,
                        column=template_column + len(setting) + value_offset,
                        path=path,
                    )
                    if issue
                    else NO_ISSUE,
                )
                for template, template_column, requirements, issue, setting, value, value_offset in zip_with_template(
                    (
                        *(
                            (template, value_column)
                            for template, _, value_column in SETTING_VALUE_CHECK_TEMPLATES
                        ),
                    ),
                    (
                        # SCP41 unneeded import path
                        *(
                            (requirements, NO_ISSUE, settings, value, 0)
                            for requirements in ("scrapy==2.3.0", "scrapy==2.4.0")
                            for settings, value in (
                                # Optional callable
                                ("FEED_URI_PARAMS", "feed_uri_params"),
                                # Special settings.
                                (
                                    "FEEDS",
                                    '{foo: {"uri_params": None}}',
                                ),
                                (
                                    "FEEDS",
                                    '{foo: {"uri_params": uri_params}}',
                                ),
                            )
                        ),
                        *(
                            ("scrapy==2.4.0", NO_ISSUE, settings, value, 0)
                            for settings, value in (
                                # Object
                                ("DEFAULT_ITEM_CLASS", "MyItem"),
                                # Based object dict
                                (
                                    "FEED_EXPORTERS",
                                    '{"json": None, "csv": MyCSVExporter}',
                                ),
                                (
                                    "FEED_EXPORTERS",
                                    "dict(json=None, csv=MyCSVExporter)",
                                ),
                                # Based component priority dict
                                (
                                    "DOWNLOADER_MIDDLEWARES",
                                    '{"scrapy.downloadermiddlewares.httpauth.HttpAuthMiddleware": None, Foo: 0}',
                                ),
                            )
                        ),
                        # SCP56 unsupported class object
                        *(
                            (
                                "scrapy==2.3.0",
                                "SCP56 unsupported class object: requires Scrapy 2.4.0+",
                                settings,
                                value,
                                value_offset,
                            )
                            for settings, value, value_offset in (
                                # Object
                                ("DEFAULT_ITEM_CLASS", "MyItem", 0),
                                ("DEFAULT_ITEM_CLASS", "items.MyItem", 0),
                                # Based object dict
                                ("FEED_EXPORTERS", '{"csv": MyCSVExporter}', 8),
                                ("FEED_EXPORTERS", "dict(csv=MyCSVExporter)", 9),
                                # Based component priority dict
                                ("DOWNLOADER_MIDDLEWARES", "{MyMiddleware: 0}", 1),
                            )
                        ),
                        # Names that do not follow the class naming convention
                        # could be variables holding an import path.
                        *(
                            ("scrapy==2.3.0", NO_ISSUE, settings, value, 0)
                            for settings, value in (
                                ("DEFAULT_ITEM_CLASS", "MY_ITEM"),
                                ("DEFAULT_ITEM_CLASS", "my_item"),
                                ("DEFAULT_ITEM_CLASS", "items.MY_ITEM"),
                                ("DEFAULT_ITEM_CLASS", "get_item_class()"),
                                # Callables can be named like variables.
                                ("FEED_URI_PARAMS", "FeedURIParams"),
                            )
                        ),
                        *(
                            (requirements, issues, settings, value, value_offset)
                            for requirements, issues in (
                                ("scrapy==2.3.0", NO_ISSUE),
                                ("scrapy==2.4.0", "SCP41 unneeded import path"),
                            )
                            for settings, value, value_offset in (
                                # Callable.
                                ("DEFAULT_ITEM_CLASS", "'my_project.items.MyItem'", 0),
                                # Optional callable.
                                ("FEED_URI_PARAMS", "'custom.feed_uri_params'", 0),
                                # Based object dict
                                ("FEED_EXPORTERS", '{"csv": "custom.CSVExporter"}', 8),
                                ("FEED_EXPORTERS", 'dict(csv="custom.CSVExporter")', 9),
                                # Based component priority dict
                                (
                                    "DOWNLOADER_MIDDLEWARES",
                                    '{"custom.Middleware": 42}',
                                    1,
                                ),
                                # Special settings.
                                (
                                    "FEEDS",
                                    '{foo: {"uri_params": "custom.uri_params"}}',
                                    21,
                                ),
                            )
                        ),
                        *(
                            (requirements, issues, settings, value, value_offset)
                            for requirements, settings, value, value_offset, issues in (
                                # Special settings.
                                (
                                    "scrapy==2.6.0",
                                    "FEEDS",
                                    '{foo: {"item_classes": [MyItem]}}',
                                    0,
                                    NO_ISSUE,
                                ),
                                (
                                    "scrapy==2.6.0",
                                    "FEEDS",
                                    '{foo: {"item_filter": MyFilter}}',
                                    0,
                                    NO_ISSUE,
                                ),
                                (
                                    "scrapy==2.6.0",
                                    "FEEDS",
                                    '{foo: {"postprocessing": [MyPlugin]}}',
                                    0,
                                    NO_ISSUE,
                                ),
                                (
                                    "scrapy==2.6.0",
                                    "FEEDS",
                                    '{foo: {"item_classes": ["custom.Item"]}}',
                                    24,
                                    "SCP41 unneeded import path",
                                ),
                                (
                                    "scrapy==2.6.0",
                                    "FEEDS",
                                    '{foo: {"item_filter": "custom.Filter"}}',
                                    22,
                                    "SCP41 unneeded import path",
                                ),
                                (
                                    "scrapy==2.6.0",
                                    "FEEDS",
                                    '{foo: {"postprocessing": ["custom.Plugin"]}}',
                                    26,
                                    "SCP41 unneeded import path",
                                ),
                                # Unknown base key
                                (
                                    "scrapy==2.4.0",
                                    "DOWNLOADER_MIDDLEWARES",
                                    '{"custom.Middleware": 42}',
                                    1,
                                    "SCP41 unneeded import path",
                                ),
                            )
                        ),
                        # SCP42 unneeded path string
                        # SCP43 unsupported Path object
                        *(
                            (f"scrapy=={version}", issues, setting, value, 0)
                            for setting, old_version, new_version in (
                                ("HTTPCACHE_DIR", "2.7.1", "2.8.0"),
                                ("TEMPLATES_DIR", "2.7.1", "2.8.0"),
                                ("FEED_TEMPDIR", "2.7.1", "2.8.0"),
                                ("JOBDIR", "2.7.1", "2.8.0"),
                                ("FILES_STORE", "2.8.0", "2.9.0"),
                                ("IMAGES_STORE", "2.8.0", "2.9.0"),
                            )
                            for value, version, issues in (
                                ("'path'", old_version, NO_ISSUE),
                                (
                                    "Path('path')",
                                    old_version,
                                    f"SCP43 unsupported Path object: requires Scrapy {new_version}+",
                                ),
                                ("'path'", new_version, "SCP42 unneeded path string"),
                                ("Path('path')", new_version, NO_ISSUE),
                            )
                        ),
                        *(
                            (f"scrapy=={version}", issues, "FEEDS", value, 1)
                            for old_version, new_version in (("2.5.1", "2.6.0"),)
                            for value, version, issues in (
                                # No path support, no URI params
                                (
                                    "{'output.json': {'format': 'json'}}",
                                    old_version,
                                    NO_ISSUE,
                                ),
                                (
                                    "{'file:///home/user/output.json': {'format': 'json'}}",
                                    old_version,
                                    NO_ISSUE,
                                ),
                                (
                                    "{Path('output.json'): {'format': 'json'}}",
                                    old_version,
                                    "SCP43 unsupported Path object: requires Scrapy 2.6.0+",
                                ),
                                # Path support, no URI params
                                (
                                    "{'output.json': {'format': 'json'}}",
                                    new_version,
                                    "SCP42 unneeded path string",
                                ),
                                (
                                    "{'file:///home/user/output.json': {'format': 'json'}}",
                                    new_version,
                                    "SCP42 unneeded path string",
                                ),
                                (
                                    "{Path('output.json'): {'format': 'json'}}",
                                    new_version,
                                    NO_ISSUE,
                                ),
                                # No path support, URI params
                                (
                                    "{'output-%(time)s.json': {'format': 'json'}}",
                                    old_version,
                                    NO_ISSUE,
                                ),
                                (
                                    "{'file:///home/user/output-%(time)s.json': {'format': 'json'}}",
                                    old_version,
                                    NO_ISSUE,
                                ),
                                (
                                    "{Path('output-%(time)s.json'): {'format': 'json'}}",
                                    old_version,
                                    "SCP43 unsupported Path object: requires Scrapy 2.6.0+",
                                ),
                                # Path support, URI params
                                (
                                    "{'output-%(time)s.json': {'format': 'json'}}",
                                    new_version,
                                    NO_ISSUE,
                                ),
                                (
                                    "{'file:///home/user/output-%(time)s.json': {'format': 'json'}}",
                                    new_version,
                                    NO_ISSUE,
                                ),
                                (
                                    "{Path('output-%(time)s.json'): {'format': 'json'}}",
                                    new_version,
                                    "SCP43 unsupported Path object: has URI params",
                                ),
                            )
                        ),
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
