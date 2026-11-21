.. _scp79:

===================================
SCP79: Inconsistent Zyte API params
===================================

What it does
============

When using :doc:`scrapy-zyte-api <scrapy-zyte-api:index>` together with
:doc:`scrapy-poet <scrapy-poet:index>`, reports a Zyte API param that
:setting:`ZYTE_API_AUTOMAP_PARAMS` and :setting:`ZYTE_API_PROVIDER_PARAMS` do
not set to the same value.

Only params meant to apply to every request are taken into account:
``geolocation`` and ``ipType``.

The settings of a spider, i.e. :attr:`~scrapy.Spider.custom_settings`, are
checked on top of those of the settings module.


Why is this bad?
================

Each setting only reaches part of the requests of a spider:
:setting:`ZYTE_API_PROVIDER_PARAMS` reaches the requests that scrapy-poet
providers send, and :setting:`ZYTE_API_AUTOMAP_PARAMS` reaches the rest. A
param that only one of them sets silently does not apply to the requests that
the other covers, so a spider that looks like it uses a single geolocation
actually uses 2.


Example
=======

.. code-block:: python

    ZYTE_API_AUTOMAP_PARAMS = {"geolocation": "US"}

Use instead:

.. code-block:: python

    ZYTE_API_AUTOMAP_PARAMS = {"geolocation": "US"}
    ZYTE_API_PROVIDER_PARAMS = {"geolocation": "US"}
