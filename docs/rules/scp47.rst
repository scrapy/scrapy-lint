.. _scp47:

=============================
SCP47: Unimportable component
=============================

What it does
============

Reports component import paths that point to a module or an object of your
project that does not exist.


Why is this bad?
================

Scrapy fails to start when it cannot import a component.


Example
=======

.. code-block:: python
    :caption: :file:`myproject/settings.py`

    DOWNLOADER_MIDDLEWARES = {
        "myproject.middlewares.MyMiddleware": 100,
    }

If :file:`myproject/middlewares.py` defines ``MyDownloaderMiddleware``
instead, use:

.. code-block:: python
    :caption: :file:`myproject/settings.py`

    DOWNLOADER_MIDDLEWARES = {
        "myproject.middlewares.MyDownloaderMiddleware": 100,
    }
