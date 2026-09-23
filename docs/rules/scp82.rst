.. _scp82:

=====================================
SCP82: Redundant add-on setting entry
=====================================

What it does
============

Finds entries in a dict or list setting that are a perfect match for an
entry an add-on already sets, when the add-on always overwrites that
entry rather than only filling it in when missing.


Why is this bad?
================

Restating an entry an add-on always overwrites is as redundant as
restating the whole setting (see :ref:`scp17`), only for a single entry
instead of for the whole value: the project value never takes effect.

Settings whose entries an add-on only fills in when missing, such as
:setting:`DOWNLOADER_MIDDLEWARES`, are not covered by this rule.
Restating one of those entries is a deliberate way to keep it unaffected
by future changes to what the add-on fills in.


How to fix it
=============

Remove the redundant entry.


Example
=======

.. code-block:: python

    ADDONS = {"scrapy_zyte_api.Addon": 500}
    DOWNLOAD_HANDLERS = {
        "http": "scrapy_zyte_api.handler.ScrapyZyteAPIHTTPDownloadHandler",
        "ftp": "scrapy.core.downloader.handlers.ftp.FTPDownloadHandler",
    }

The add-on already sets the ``http`` entry to that same value, so it
should be removed:

.. code-block:: python

    ADDONS = {"scrapy_zyte_api.Addon": 500}
    DOWNLOAD_HANDLERS = {
        "ftp": "scrapy.core.downloader.handlers.ftp.FTPDownloadHandler",
    }
