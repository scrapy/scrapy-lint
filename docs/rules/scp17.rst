.. _scp17:

==============================
SCP17: Redundant setting value
==============================

What it does
============

Finds settings in a settings module (e.g. :file:`settings.py`) that are set to
their default value and are not :ref:`changing settings <scp34>`.

Why is this bad?
================

Setting a setting to its default value is generally unnecessary, and can be
misleading.

Do it only if the default value changes in a future version of Scrapy, you
will need to keep the current default, and you do not want to risk forgetting
about it when you actually upgrade to that future version of Scrapy.

Example
=======

.. code-block:: python

    COOKIES_ENABLED = True

:setting:`COOKIES_ENABLED` is ``True`` by default, so this setting is redundant
and should be removed.

.. code-block:: python

    ADDONS = {"scrapy_zyte_api.Addon": 500}
    ZYTE_API_TRANSPARENT_MODE = True

The add-on already sets ``ZYTE_API_TRANSPARENT_MODE`` to ``True``, so that
second line should be removed.
