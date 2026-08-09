.. _scp53:

============================
SCP53: Unneeded start method
============================

What it does
============

Reports :meth:`~scrapy.Spider.start` and ``start_requests`` implementations
that only send requests that :attr:`~scrapy.Spider.start_urls` could send.


Why is this bad?
================

:attr:`~scrapy.Spider.start_urls` is shorter, and it makes the initial URLs of
a spider easy to find, both for readers and for code that inspects spiders.


Example
=======

.. code-block:: python

    class MySpider(Spider):
        name = "my"

        async def start(self):
            yield Request("https://toscrape.com/")

Instead use:

.. code-block:: python

    class MySpider(Spider):
        name = "my"

        start_urls = ["https://toscrape.com/"]


Requests without ``dont_filter``
================================

:attr:`~scrapy.Spider.start_urls` sends requests with
:attr:`~scrapy.Request.dont_filter` enabled, so switching to it also disables
duplicate filtering for those requests.

If you implement :meth:`~scrapy.Spider.start` to keep duplicate filtering, and
that is a scenario that you expect, :ref:`disable this rule <ignore>`.


Fix
===

This rule is automatically fixable with the ``--fix`` command-line option: the
start method is replaced with an equivalent
:attr:`~scrapy.Spider.start_urls`, or removed if it only re-sends the requests
of :attr:`~scrapy.Spider.start_urls`.

To keep duplicate filtering as is, the fix only applies to requests that set
:attr:`~scrapy.Request.dont_filter` to ``True``.
