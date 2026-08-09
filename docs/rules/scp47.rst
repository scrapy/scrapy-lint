.. _scp47:

=========================
SCP47: No allowed_domains
=========================

What it does
============

Finds spider classes that define :attr:`~scrapy.Spider.start_urls` but not
:attr:`~scrapy.Spider.allowed_domains`.

Only classes that directly subclass a Scrapy spider class are checked, so a
spider that inherits :attr:`~scrapy.Spider.allowed_domains` from a base spider
class of your own is not reported.


Why is this bad?
================

Without :attr:`~scrapy.Spider.allowed_domains`, a bug in a link-following
callback can send your spider crawling any website it finds a link to, hitting
servers that never expected your traffic.

If your spider is meant to crawl an open-ended set of domains, disable this
rule with :ref:`ignore` or :ref:`per-file-ignores`.


Example
=======

.. code-block:: python

    import scrapy


    class MySpider(scrapy.Spider):
        name = "myspider"
        start_urls = [
            "https://a.example/",
        ]

Use instead:

.. code-block:: python

    import scrapy


    class MySpider(scrapy.Spider):
        name = "myspider"
        allowed_domains = ["a.example"]
        start_urls = [
            "https://a.example/",
        ]
