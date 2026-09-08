.. _scp47:

========================
SCP47: Lowercase setting
========================

What it does
============

Reports a setting name in a setting module (e.g. ``settings.py``) that is not
uppercase but matches a :ref:`known setting of Scrapy itself <topics-settings>`
or of a known `Scrapy plugin`_, or a :ref:`known-settings` entry, once
uppercased.

.. _Scrapy plugin: https://github.com/scrapy-plugins


Why is this bad?
================

Scrapy only reads uppercase names from setting modules, so a setting written
with the wrong case is silently ignored and its intended value is never
applied, which can lead to bugs or unexpected behavior. It may also break
third-party tooling that expects settings to be uppercase.


Example
=======

The following code will trigger SCP47, because ``robotstxt_obey`` is ignored
by Scrapy and :setting:`ROBOTSTXT_OBEY` keeps its default value:

.. code-block:: python
    :caption: ``settings.py``

    robotstxt_obey = True

Use the uppercase setting name instead:

.. code-block:: python
    :caption: ``settings.py``

    ROBOTSTXT_OBEY = True
