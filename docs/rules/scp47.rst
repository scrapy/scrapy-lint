.. _scp47:

======================================
SCP47: start_url instead of start_urls
======================================

What it does
============

Finds a ``start_url`` attribute in a class that does not define
:attr:`~scrapy.Spider.start_urls`.


Why is this bad?
================

Scrapy reads :attr:`~scrapy.Spider.start_urls`, so a spider that defines
``start_url`` instead crawls nothing.


Example
=======

.. code-block:: python

    import scrapy


    class MySpider(scrapy.Spider):
        name = "myspider"
        start_url = "https://toscrape.com"

Use instead:

.. code-block:: python

    import scrapy


    class MySpider(scrapy.Spider):
        name = "myspider"
        start_urls = ["https://toscrape.com"]


Fix
===

This rule is automatically fixable with the ``--fix`` command-line option:
the attribute is renamed, and its value wrapped in a list if needed.
