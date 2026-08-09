.. _scp58:

============================
SCP58: Documentation comment
============================

What it does
============

Finds `documentation comments
<https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#doc-comments-and-docstrings>`_
(``#:``) on the fields of an item class.


Why is this bad?
================

`itemadapter <https://github.com/scrapy/itemadapter>`_ builds the
``description`` of each property of an item JSON Schema from the docstring
that follows the corresponding field, and ignores documentation comments.


Example
=======

.. code-block:: python

    import scrapy


    class ProductItem(scrapy.Item):
        #: Product name.
        name = scrapy.Field()

Use instead:

.. code-block:: python

    import scrapy


    class ProductItem(scrapy.Item):
        name = scrapy.Field()
        """Product name."""


Fix
===

This rule is automatically fixable with the ``--fix`` command-line option:
a documentation comment above a field becomes a docstring below it.
