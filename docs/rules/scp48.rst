.. _scp48:

==========================
SCP48: Old selector getter
==========================

What it does
============

Finds calls to ``extract()`` on the result of
:meth:`~scrapy.selector.SelectorList.css` or
:meth:`~scrapy.selector.SelectorList.xpath`.


Why is this bad?
================

:meth:`~scrapy.selector.SelectorList.getall` is the current name of that
method, and the one that pairs with
:meth:`~scrapy.selector.SelectorList.get`.


Example
=======

.. code-block:: python

    import scrapy


    class MySpider(scrapy.Spider):
        name = "myspider"

        def parse(self, response):
            yield {"titles": response.css("h1::text").extract()}

Use instead:

.. code-block:: python

    import scrapy


    class MySpider(scrapy.Spider):
        name = "myspider"

        def parse(self, response):
            yield {"titles": response.css("h1::text").getall()}


Fix
===

This rule is automatically fixable with the ``--fix`` command-line option:
``extract()`` is renamed to ``getall()``.
