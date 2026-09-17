.. _scp02:

====================================
SCP02: Invalid allowed_domains entry
====================================

What it does
============

Finds URLs or domains with a port in :attr:`~scrapy.Spider.allowed_domains`.


Why is this bad?
================

The :attr:`~scrapy.Spider.allowed_domains` attribute should contain domain names
only. A domain that carries a port never matches any request, so it is silently
not allowed.


Example
=======

.. code-block:: python

    import scrapy


    class MySpider(scrapy.Spider):
        name = "myspider"
        allowed_domains = ["https://toscrape.com/", "127.0.0.1:8080"]

Use instead:

.. code-block:: python

    import scrapy


    class MySpider(scrapy.Spider):
        name = "myspider"
        allowed_domains = ["toscrape.com", "127.0.0.1"]


Fix
===

This rule is automatically fixable with the ``--fix`` command-line option:
each value is replaced with its bare domain.
