.. _scp48:

==================================
SCP48: Deprecated spider attribute
==================================

What it does
============

Reports spider attributes that are deprecated for the Scrapy version frozen in
your project requirements.

It also reports the version in which the attribute was deprecated, and the
setting to use instead.


Why is this bad?
================

Deprecated spider attributes will stop working in future versions of Scrapy.

If you do not migrate now, the next time you upgrade Scrapy your project could
break or misbehave.


How to fix it?
==============

Move the value to the matching setting, usually through
:attr:`~scrapy.Spider.custom_settings`. For example, instead of:

.. code-block:: python

    class ToScrapeComSpider(Spider):
        name = "toscrape_com"
        download_timeout = 15

Do:

.. code-block:: python

    class ToScrapeComSpider(Spider):
        name = "toscrape_com"
        custom_settings = {"DOWNLOAD_TIMEOUT": 15}

Mind that a setting has a different scope than a spider attribute: code that
reads the attribute from the spider object needs to read the setting instead.
