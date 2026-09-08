.. _scp51:

==========================
SCP51: Deprecated argument
==========================

What it does
============

Reports parameters of component methods that are deprecated for the Scrapy
version frozen in your project requirements.

It also reports the version in which the parameter was deprecated, and what to
use instead.

Currently, the only deprecated parameter is ``spider``, in methods that Scrapy
calls on your components: ``process_request()``, ``process_response()``,
``process_exception()``, ``process_spider_input()``, ``process_spider_output()``,
``process_spider_exception()``, ``process_item()``, ``open_spider()``,
``close_spider()`` and ``fetch()``.


Why is this bad?
================

Scrapy will stop passing the ``spider`` argument to these methods, and calling
them will then fail.


How to fix it?
==============

Drop the argument. For example, instead of:

.. code-block:: python

    class MyPipeline:
        def process_item(self, item, spider):
            return item

Do:

.. code-block:: python

    class MyPipeline:
        def process_item(self, item):
            return item

If you do need the spider, get it from the crawler:

.. code-block:: python

    class MyPipeline:
        @classmethod
        def from_crawler(cls, crawler):
            return cls(crawler)

        def __init__(self, crawler):
            self.crawler = crawler

        def process_item(self, item):
            self.crawler.spider.logger.info("Got an item")
            return item

To support older Scrapy versions as well, give the argument a default value:

.. code-block:: python

    class MyPipeline:
        def process_item(self, item, spider=None):
            return item
