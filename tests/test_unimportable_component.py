from __future__ import annotations

from tests.helpers import check_project

from . import NO_ISSUE, Cases, ExpectedIssue, File, cases

PATH = "a.py"
PROJECT_FILES = (
    File("", path="myproject/__init__.py"),
    File("class MyMiddleware:\n    pass\n", path="myproject/middlewares.py"),
)
UNIMPORTABLE_COMPONENT = ExpectedIssue(
    "SCP47 unimportable component",
    column=31,
    path=PATH,
)

CASES: Cases = (
    *(
        (
            (*PROJECT_FILES, *extra_files, File(code, path=PATH)),
            issues,
            {},
        )
        for extra_files, code, issues in (
            # Objects of the project are resolved through its Python files.
            (
                (),
                "settings['DUPEFILTER_CLASS'] = 'myproject.middlewares.MyMiddleware'",
                NO_ISSUE,
            ),
            (
                (),
                "settings['DUPEFILTER_CLASS'] = 'myproject.middlewares.Middleware'",
                UNIMPORTABLE_COMPONENT,
            ),
            (
                (),
                "settings['DUPEFILTER_CLASS'] = 'myproject.middleware.MyMiddleware'",
                UNIMPORTABLE_COMPONENT,
            ),
            # Modules of the project are components as well.
            (
                (),
                "settings['DUPEFILTER_CLASS'] = 'myproject.middlewares'",
                NO_ISSUE,
            ),
            # Objects outside the project are out of scope.
            (
                (),
                "settings['DUPEFILTER_CLASS'] = 'scrapy_poet.addons.Addon'",
                NO_ISSUE,
            ),
            # Attributes of an object are not resolved.
            (
                (),
                "settings['DUPEFILTER_CLASS'] = "
                "'myproject.middlewares.MyMiddleware.from_crawler'",
                NO_ISSUE,
            ),
            # Names imported into a module count as objects of that module.
            (
                (File("from .middlewares import MyMiddleware", path="myproject/a.py"),),
                "settings['DUPEFILTER_CLASS'] = 'myproject.a.MyMiddleware'",
                NO_ISSUE,
            ),
            (
                (File("MyMiddleware = object", path="myproject/a.py"),),
                "settings['DUPEFILTER_CLASS'] = 'myproject.a.MyMiddleware'",
                NO_ISSUE,
            ),
            # Unparseable modules make their objects unknown.
            (
                (
                    File("myproject/a.py", path=".gitignore"),
                    File("class", path="myproject/a.py"),
                ),
                "settings['DUPEFILTER_CLASS'] = 'myproject.a.MyMiddleware'",
                NO_ISSUE,
            ),
            # Star imports make the objects of a module unknown.
            (
                (File("from foo import *", path="myproject/a.py"),),
                "settings['DUPEFILTER_CLASS'] = 'myproject.a.MyMiddleware'",
                NO_ISSUE,
            ),
            # Namespace packages, which may extend beyond the project, are
            # unknown.
            (
                (File("", path="myproject/a/b.py"),),
                "settings['DUPEFILTER_CLASS'] = 'myproject.a.MyMiddleware'",
                NO_ISSUE,
            ),
        )
    ),
    # Component priority dicts are checked as well.
    (
        (
            *PROJECT_FILES,
            File(
                "settings['DOWNLOADER_MIDDLEWARES'] = "
                "{'myproject.middlewares.Middleware': 100}",
                path=PATH,
            ),
        ),
        ExpectedIssue("SCP47 unimportable component", column=38, path=PATH),
        {},
    ),
)


@cases(CASES)
def test(files, expected, options):
    check_project(files, expected, options)
