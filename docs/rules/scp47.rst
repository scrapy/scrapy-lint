.. _scp47:

========================
SCP47: Lowercase setting
========================

What it does
============

Reports assignments in a setting module (e.g. ``settings.py``) whose name is
not uppercase but matches a :ref:`known setting <scp27>` when uppercased, such
as ``robotstxt_obey`` instead of :setting:`ROBOTSTXT_OBEY`.


Why is this bad?
================

Scrapy only reads uppercase names from setting modules. A setting written with
a lowercase or mixed-case name is silently ignored, so your intended
configuration is not applied, which can lead to bugs or unexpected behavior. It
may also break third-party tooling that expects settings to be uppercase.

Unlike :ref:`scp27`, which reports unknown uppercase names, this rule catches
names that *would* be valid settings if they were uppercase.


Example
=======

The following code will trigger SCP47, because ``robotstxt_obey`` is ignored by
Scrapy and :setting:`ROBOTSTXT_OBEY` remains at its default value:

.. code-block:: python
    :caption: ``settings.py``

    robotstxt_obey = True

Use the uppercase setting name instead:

.. code-block:: python
    :caption: ``settings.py``

    ROBOTSTXT_OBEY = True
