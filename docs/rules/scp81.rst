.. _scp81:

=====================================
SCP81: Invalid component deactivation
=====================================

What it does
============

Reports keys of component priority dictionaries, such as
:setting:`DOWNLOADER_MIDDLEWARES`, that are set to ``None`` to disable a
component that Scrapy enables by default, but that are objects instead of the
import path string used in the corresponding base setting, e.g.
:setting:`DOWNLOADER_MIDDLEWARES_BASE`, in projects frozen to a Scrapy version
older than 2.15.0.


Why is this bad?
================

Before Scrapy 2.15.0, the base setting and the project setting are merged by
key. An object key never matches the import path string of the base setting,
so the component stays enabled and nothing reports it.


How to fix it
=============

Use the import path string of the component as the key, or upgrade to Scrapy
2.15.0 or later, which matches keys by the object they import.


Example
=======

.. code-block:: python

    from scrapy.downloadermiddlewares.retry import RetryMiddleware

    DOWNLOADER_MIDDLEWARES = {
        RetryMiddleware: None,
    }

Use instead:

.. code-block:: python

    DOWNLOADER_MIDDLEWARES = {
        "scrapy.downloadermiddlewares.retry.RetryMiddleware": None,
    }
