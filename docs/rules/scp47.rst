.. _scp47:

=======================
SCP47: No @attrs.define
=======================

What it does
============

Reports :doc:`page objects <web-poet:page-objects/index>` that declare
attributes without an :func:`attrs.define` decorator.

Only page objects that subclass a :doc:`web-poet <web-poet:index>` class
directly are reported, since the base classes of a page object that subclasses
a page object of your own cannot be determined reliably.


Why is this bad?
================

A page object declares its dependencies as class attributes, and
:doc:`scrapy-poet <scrapy-poet:index>` fills them in when it builds the page
object. Without an :func:`attrs.define` decorator, those attributes are plain
annotations, so nothing is injected and reading them raises
:exc:`AttributeError` at run time.


Example
=======

Instead of:

.. code-block:: python

    from web_poet import Stats, WebPage


    class MyPage(WebPage):
        stats: Stats

Use:

.. code-block:: python

    import attrs
    from web_poet import Stats, WebPage


    @attrs.define
    class MyPage(WebPage):
        stats: Stats
