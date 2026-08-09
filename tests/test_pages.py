from __future__ import annotations

from inspect import cleandoc
from typing import TYPE_CHECKING

import pytest

from . import NO_ISSUE, Cases, ExpectedIssue, File, cases
from .helpers import check_project, fix_project

if TYPE_CHECKING:
    from collections.abc import Sequence

PATH = "pages.py"


def code(text: str) -> str:
    return cleandoc(text) + "\n"


ISSUE = ExpectedIssue("SCP47 no @attrs.define", column=6, path=PATH)

CASES: Cases = tuple(
    (File(code(source), path=PATH), expected, {})
    for source, expected in (
        # A page object that declares an attribute needs the decorator.
        (
            """
            from web_poet import Stats, WebPage
            class MyPage(WebPage):
                stats: Stats
            """,
            ISSUE.replace(line=2),
        ),
        # Import paths and aliases are resolved.
        (
            """
            from web_poet.pages import WebPage as Base
            class MyPage(Base):
                stats: Stats
            """,
            ISSUE.replace(line=2),
        ),
        (
            """
            import web_poet
            class MyPage(web_poet.ItemPage):
                stats: web_poet.Stats
            """,
            ISSUE.replace(line=2),
        ),
        (
            """
            import web_poet.pages as pages
            class MyPage(pages.Injectable):
                stats: Stats
            """,
            ISSUE.replace(line=2),
        ),
        # A generic subscript does not hide the base class.
        (
            """
            from web_poet import WebPage
            from myproject.items import MyItem
            class MyPage(WebPage[MyItem]):
                stats: Stats
            """,
            ISSUE.replace(line=3),
        ),
        # A base class that is not a web-poet one is out of scope, be it a page
        # object of the project, a class that only shares the name of a web-poet
        # one, or an unrelated class.
        (
            """
            from myproject.pages import BasePage
            class MyPage(BasePage):
                stats: Stats
            """,
            NO_ISSUE,
        ),
        (
            """
            from myproject.base import WebPage
            class MyPage(WebPage):
                stats: Stats
            """,
            NO_ISSUE,
        ),
        (
            """
            from .base import WebPage
            class MyPage(WebPage):
                stats: Stats
            """,
            NO_ISSUE,
        ),
        (
            """
            from django.db.models import Model
            class MyModel(Model):
                name: str
            """,
            NO_ISSUE,
        ),
        # An unimported or computed base class cannot be resolved.
        (
            """
            class MyPage(WebPage):
                stats: Stats
            """,
            NO_ISSUE,
        ),
        (
            """
            from myproject.pages import page_base
            class MyPage(page_base()):
                stats: Stats
            """,
            NO_ISSUE,
        ),
        # Any decorator that turns annotations into fields is enough.
        *(
            (
                f"""
                import attrs
                from web_poet import WebPage
                {decorator}
                class MyPage(WebPage):
                    stats: Stats
                """,
                NO_ISSUE,
            )
            for decorator in (
                "@attrs.define",
                "@attrs.frozen",
                "@attrs.mutable",
                "@attrs.define(slots=False)",
                "@attr.s(auto_attribs=True)",
                "@define",
                "@dataclass",
            )
        ),
        # An unrelated decorator is not.
        (
            """
            from typing import final
            from web_poet import WebPage
            @final
            class MyPage(WebPage):
                stats: Stats
            """,
            ISSUE.replace(line=4),
        ),
        # A page object that declares no attributes needs no decorator.
        (
            """
            from web_poet import WebPage
            class MyPage(WebPage):
                async def to_item(self):
                    return {}
            """,
            NO_ISSUE,
        ),
        # Class variables are not attributes.
        (
            """
            import typing
            from typing import ClassVar
            from web_poet import WebPage
            class MyPage(WebPage):
                a: ClassVar[int] = 1
                b: typing.ClassVar = 2
            """,
            NO_ISSUE,
        ),
        # Annotations under TYPE_CHECKING are not attribute declarations.
        (
            """
            from typing import TYPE_CHECKING
            from web_poet import WebPage
            class MyPage(WebPage):
                if TYPE_CHECKING:
                    stats: Stats
            """,
            NO_ISSUE,
        ),
        # Inner classes are covered too.
        (
            """
            from web_poet import WebPage
            class Outer:
                class MyPage(WebPage):
                    stats: Stats
            """,
            ISSUE.replace(line=3, column=10),
        ),
    )
)


@cases(CASES)
def test(
    files: File | Sequence[File],
    expected: ExpectedIssue | Sequence[ExpectedIssue] | None,
    options,
):
    check_project(files, expected, options)


# (source, expected output, number of issues fixed)
FIX_CASES = (
    # The decorator is added, along with the import it needs.
    (
        """
        from web_poet import Stats, WebPage
        class MyPage(WebPage):
            stats: Stats
        """,
        """
        import attrs
        from web_poet import Stats, WebPage
        @attrs.define
        class MyPage(WebPage):
            stats: Stats
        """,
        1,
    ),
    # An existing attrs import is reused, and every page object in the file is
    # decorated.
    (
        """
        import attrs
        from web_poet import Stats, WebPage
        class One(WebPage):
            stats: Stats
        @attrs.define
        class Two(WebPage):
            stats: Stats
        class Three(WebPage):
            stats: Stats
        """,
        """
        import attrs
        from web_poet import Stats, WebPage
        @attrs.define
        class One(WebPage):
            stats: Stats
        @attrs.define
        class Two(WebPage):
            stats: Stats
        @attrs.define
        class Three(WebPage):
            stats: Stats
        """,
        2,
    ),
    # The import is added once, and never before a __future__ import.
    (
        """
        from __future__ import annotations
        from web_poet import Stats, WebPage
        class One(WebPage):
            stats: Stats
        class Two(WebPage):
            stats: Stats
        """,
        """
        from __future__ import annotations
        import attrs
        from web_poet import Stats, WebPage
        @attrs.define
        class One(WebPage):
            stats: Stats
        @attrs.define
        class Two(WebPage):
            stats: Stats
        """,
        2,
    ),
    # Indentation is preserved.
    (
        """
        from web_poet import Stats, WebPage
        class Outer:
            class MyPage(WebPage):
                stats: Stats
        """,
        """
        import attrs
        from web_poet import Stats, WebPage
        class Outer:
            @attrs.define
            class MyPage(WebPage):
                stats: Stats
        """,
        1,
    ),
)


@pytest.mark.parametrize(
    ("source", "expected", "fixed"),
    FIX_CASES,
    ids=range(len(FIX_CASES)),
)
def test_fix(source: str, expected: str, fixed: int):
    fix_project(
        File(code(source), path=PATH),
        File(code(expected), path=PATH),
        expected_fixed=fixed,
    )
