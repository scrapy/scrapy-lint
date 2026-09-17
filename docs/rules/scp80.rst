.. _scp80:

=========================
SCP80: Wrong add-on order
=========================

What it does
============

Reports add-ons in the ``ADDONS`` setting that Scrapy runs before an add-on
that they need to run after.

Scrapy runs add-ons sorted by their priority value, and add-ons sharing a
priority value run in definition order.


Why is this bad?
================

Add-ons that build on the setting values that other add-ons set need to run
after them. When they do not, they overwrite those values instead, and nothing
reports it at run time.

For example, the add-ons of duplicate-url-discarder, scrapy-poet and
scrapy-zyte-api all set ``REQUEST_FINGERPRINTER_CLASS``, each wrapping the
request fingerprinter that was set before it. In the wrong order, request
fingerprinting silently stops taking into account what one of them contributes.


How to fix it
=============

Give the add-on that must run last a higher priority value.


Example
=======

.. code-block:: python

    ADDONS = {
        "duplicate_url_discarder.Addon": 100,
        "scrapy_zyte_api.Addon": 200,
    }


Use instead:

.. code-block:: python

    ADDONS = {
        "scrapy_zyte_api.Addon": 100,
        "duplicate_url_discarder.Addon": 200,
    }
