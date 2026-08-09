.. _scp47:

====================================
SCP47: Missing component requirement
====================================

What it does
============

Reports component import paths in setting values that belong to packages that
are missing from your :ref:`project requirements <requirements>`.


Why is this bad?
================

Such components cannot be imported at run time.


Example
=======

.. code-block:: python

    DOWNLOADER_MIDDLEWARES = {
        "scrapy_zyte_api.ScrapyZyteAPIDownloaderMiddleware": 633,
    }

Add ``scrapy-zyte-api`` to your project requirements.
