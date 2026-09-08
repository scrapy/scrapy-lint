.. _scp47:

========================
SCP47: Non-spider logger
========================

What it does
============

Reports the use of a logger other than :attr:`~scrapy.Spider.logger` in the
methods of a spider class.


Why is this bad?
================

:attr:`~scrapy.Spider.logger` binds every log record to the spider that wrote
it. Records written through a module-level logger, or through the
:mod:`logging` module itself, are not bound to any spider, so the ``spider``
part of :setting:`LOG_FORMAT` renders as ``None`` and the record is logged
under the name of the module instead of the name of the spider. In a project
with more than one spider, that makes logs much harder to follow.

Note that :attr:`~scrapy.Spider.logger` logs under the name of the spider, so
if you configure logging levels per module, you lose that granularity for
spider code.


Example
=======

.. code-block:: python

    import logging

    import scrapy

    logger = logging.getLogger(__name__)


    class MySpider(scrapy.Spider):
        name = "myspider"

        def parse(self, response):
            logger.info(f"Parsing {response.url}")

Use instead:

.. code-block:: python

    import scrapy


    class MySpider(scrapy.Spider):
        name = "myspider"

        def parse(self, response):
            self.logger.info(f"Parsing {response.url}")

Alternatively, pass the spider in the ``extra`` dictionary of the log call,
which this rule also accepts:

.. code-block:: python

    logger.info(f"Parsing {response.url}", extra={"spider": self})


Fix
===

This rule is automatically fixable with the ``--fix`` command-line option: the
logger is replaced with :attr:`~scrapy.Spider.logger`.
