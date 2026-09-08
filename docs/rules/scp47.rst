.. _scp47:

========================
SCP47: Uncached urlparse
========================

What it does
============

Finds usage of :func:`~urllib.parse.urlparse` on the URL of a request or a
response that can be replaced with
:func:`~scrapy.utils.httpobj.urlparse_cached`.


Why is this bad?
================

:func:`~scrapy.utils.httpobj.urlparse_cached` caches its result on the request
or response object, so parsing the same URL again, in your code or in Scrapy
itself, costs nothing. Scrapy parses the URL of every request it sends, so for
requests the cache is usually warm already.


Example
=======

.. code-block:: python

    import scrapy
    from urllib.parse import urlparse


    class MySpider(scrapy.Spider):
        name = "myspider"

        def parse(self, response):
            yield {"hostname": urlparse(response.url).hostname}

Use instead:

.. code-block:: python

    import scrapy
    from scrapy.utils.httpobj import urlparse_cached


    class MySpider(scrapy.Spider):
        name = "myspider"

        def parse(self, response):
            yield {"hostname": urlparse_cached(response).hostname}


Fix
===

This rule is automatically fixable with the ``--fix`` command-line option: the
call is replaced and :func:`~scrapy.utils.httpobj.urlparse_cached` is imported.
An :func:`~urllib.parse.urlparse` import that the fix leaves unused is kept.
