.. _scp49:

========================================
SCP49: Absolute XPath in nested selector
========================================

What it does
============

Finds XPath expressions that start with ``/`` in a
:meth:`~scrapy.selector.SelectorList.xpath` call made on the result of a
:meth:`~scrapy.selector.SelectorList.css` or
:meth:`~scrapy.selector.SelectorList.xpath` call.

Selectors stored in a variable, such as the target of a ``for`` loop, are not
reported, since there is no way to tell whether they are nested selectors or
root ones.


Why is this bad?
================

An XPath expression that starts with ``/``, including one that starts with
``//``, is evaluated from the root of the document, so it ignores the selector
it is called on and matches nodes anywhere in the document.

See :ref:`topics-selectors-relative-xpaths` in the Scrapy documentation.


Example
=======

.. code-block:: python

    import scrapy


    class MySpider(scrapy.Spider):
        name = "myspider"

        def parse(self, response):
            yield {"links": response.css("article").xpath("//a/@href").getall()}

Use instead:

.. code-block:: python

    import scrapy


    class MySpider(scrapy.Spider):
        name = "myspider"

        def parse(self, response):
            yield {"links": response.css("article").xpath(".//a/@href").getall()}
