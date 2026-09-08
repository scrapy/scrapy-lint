from __future__ import annotations

from inspect import cleandoc

from . import NO_ISSUE, Cases, ExpectedIssue, File, cases
from .helpers import check_project

PATH = "a.py"
MESSAGE = "SCP47 non-spider logger"


def spider(statement: str) -> str:
    """Return a spider module whose ``parse`` method runs *statement*, which
    lands on line 6, column 8."""
    return (
        cleandoc(
            f"""
            logger = logging.getLogger(__name__)


            class MySpider(Spider):
                def parse(self, response):
                    {statement}
            """,
        )
        + "\n"
    )


def issue(line: int = 6, column: int = 8) -> ExpectedIssue:
    return ExpectedIssue(message=MESSAGE, line=line, column=column, path=PATH)


CASES: Cases = (
    *(
        (File(spider(statement), path=PATH), expected, {})
        for statement, expected in (
            # Baseline
            *(
                (statement, NO_ISSUE)
                for statement in (
                    'self.logger.info("a")',
                    'self.log("a")',
                    # Not a logger.
                    'response.info("a")',
                    # Not a logging call.
                    "logger.setLevel(DEBUG)",
                    # Already bound to the spider.
                    'logger.info("a", extra={"spider": self})',
                    # Bound to something we cannot inspect.
                    'logger.info("a", extra=extra)',
                    # Logger built in place, out of scope.
                    'logging.getLogger("a").info("b")',
                )
            ),
            *(
                (statement, issue())
                for statement in (
                    'logger.info("a")',
                    'logger.log(INFO, "a")',
                    'logger.exception("a")',
                    # The root logger has the same problem.
                    'logging.warning("a")',
                    'logger.info("a", extra={"foo": "bar"})',
                    'logger.info("a", **kwargs)',
                )
            ),
        )
    ),
    # Any base class named after a spider counts.
    *(
        (
            File(
                cleandoc(
                    f"""
                    logger = logging.getLogger(__name__)


                    class MySpider({base}):
                        def parse(self, response):
                            logger.info("a")
                    """,
                )
                + "\n",
                path=PATH,
            ),
            issue(),
            {},
        )
        for base in ("scrapy.Spider", "CrawlSpider", "BaseSpider")
    ),
    # Loggers imported from the logging module directly.
    (
        File(
            cleandoc(
                """
                log = getLogger(__name__)


                class MySpider(Spider):
                    def parse(self, response):
                        log.info("a")
                """,
            )
            + "\n",
            path=PATH,
        ),
        issue(),
        {},
    ),
    # Nested functions still have self in scope.
    (
        File(
            cleandoc(
                """
                logger = logging.getLogger(__name__)


                class MySpider(Spider):
                    def parse(self, response):
                        def callback(response):
                            logger.info("a")
                """,
            )
            + "\n",
            path=PATH,
        ),
        issue(line=7, column=12),
        {},
    ),
    # Components other than spiders have no self.logger.
    *(
        (
            File(
                cleandoc(
                    f"""
                    logger = logging.getLogger(__name__)


                    class MyPipeline{bases}:
                        def process_item(self, item, spider):
                            logger.info("a")
                    """,
                )
                + "\n",
                path=PATH,
            ),
            NO_ISSUE,
            {},
        )
        for bases in ("", "(Generic[T])")
    ),
    # Methods without self cannot use self.logger either.
    (
        File(
            cleandoc(
                """
                logger = logging.getLogger(__name__)


                class MySpider(Spider):
                    @classmethod
                    def from_crawler(cls, crawler, *args, **kwargs):
                        logger.info("a")
                """,
            )
            + "\n",
            path=PATH,
        ),
        NO_ISSUE,
        {},
    ),
    # Module-level code is not spider code.
    (
        File(
            cleandoc(
                """
                logger = logging.getLogger(__name__)

                logger.info("a")
                """,
            )
            + "\n",
            path=PATH,
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
