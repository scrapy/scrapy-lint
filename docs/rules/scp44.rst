.. _scp44:

===============================
SCP44: Unsupported class object
===============================

What it does
============

Reports the use of classes instead of import path strings in setting values,
when using a version of Scrapy older than :ref:`release-2.4.0`.

A name is assumed to be a class if it starts with an uppercase letter and
contains a lowercase one. Settings that expect any callable, such as
:setting:`FEED_URI_PARAMS`, are not reported, since functions are named like
variables that could hold an import path.


Why is this bad?
================

Before :ref:`release-2.4.0`, settings that expect a class only accept its
import path as a string, so passing the class itself leads to run time errors.


Example
=======

.. code-block:: python

    import scrapy_poet

    DOWNLOADER_MIDDLEWARES = {
        scrapy_poet.InjectionMiddleware: 543,
    }

Instead use:

.. code-block:: python

    DOWNLOADER_MIDDLEWARES = {
        "scrapy_poet.InjectionMiddleware": 543,
    }
