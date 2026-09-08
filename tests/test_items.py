from __future__ import annotations

from inspect import cleandoc

from . import NO_ISSUE, Cases, ExpectedIssue, File, cases
from .helpers import check_project

CASES: Cases = (
    # A documentation comment above a Scrapy item field.
    (
        (
            File(
                cleandoc(
                    """
                    class ProductItem(scrapy.Item):
                        #: Product name.
                        name = scrapy.Field()
                    """,
                ),
                path="a.py",
            ),
        ),
        ExpectedIssue(
            message="SCP58 documentation comment",
            line=2,
            column=4,
            path="a.py",
        ),
        {},
    ),
    # A documentation comment on the same line as the field.
    (
        (
            File(
                cleandoc(
                    """
                    class ProductItem(Item):
                        name = scrapy.Field()  #: Product name.
                    """,
                ),
                path="a.py",
            ),
        ),
        ExpectedIssue(
            message="SCP58 documentation comment",
            line=2,
            column=27,
            path="a.py",
        ),
        {},
    ),
    # A multi-line block counts as a single documentation comment.
    (
        (
            File(
                cleandoc(
                    """
                    @attrs.define
                    class Product:
                        #: Product name,
                        #: as advertised.
                        name: str
                    """,
                ),
                path="a.py",
            ),
        ),
        ExpectedIssue(
            message="SCP58 documentation comment",
            line=3,
            column=4,
            path="a.py",
        ),
        {},
    ),
    # Dataclass and Pydantic items are covered as well.
    (
        (
            File(
                cleandoc(
                    """
                    @dataclass
                    class Product:
                        #: Product name.
                        name: str

                    class Offer(BaseModel):
                        #: Price.
                        price: float
                    """,
                ),
                path="a.py",
            ),
        ),
        (
            ExpectedIssue(
                message="SCP58 documentation comment",
                line=3,
                column=4,
                path="a.py",
            ),
            ExpectedIssue(
                message="SCP58 documentation comment",
                line=7,
                column=4,
                path="a.py",
            ),
        ),
        {},
    ),
    # Docstrings, plain comments, comments outside an item class and
    # comments not attached to a field are all fine.
    (
        (
            File(
                cleandoc(
                    """
                    #: Module-level noise.
                    x = 1


                    class MySpider(scrapy.Spider):
                        #: Not an item field.
                        name = "myspider"


                    class ProductItem(scrapy.Item):
                        # Plain comment.
                        name = scrapy.Field()
                        \"\"\"Product name.\"\"\"

                        #: Dangling, documents nothing.


                    class Container(Generic[T]):
                        #: Not an item field either.
                        name: str
                    """,
                ),
                path="a.py",
            ),
        ),
        NO_ISSUE,
        {},
    ),
)


@cases(CASES)
def test(
    files: File | list[File],
    expected: ExpectedIssue | list[ExpectedIssue] | None,
    options,
):
    check_project(files, expected, options)
