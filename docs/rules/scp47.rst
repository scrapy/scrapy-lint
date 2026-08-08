.. _scp47:

=====================
SCP47: Missing add-on
=====================

What it does
============

Reports requirements that provide an :ref:`add-on <topics-addons>` which is not
enabled in the :setting:`ADDONS` setting of your settings module (e.g.
:file:`settings.py`).


Why is this bad?
================

Add-ons configure everything that their package needs, and keep that
configuration up to date as the package evolves. Configuring the same package
manually means more code in your settings module, and settings that you must
review and update on every upgrade of that package.


How to fix it
=============

Enable the add-on, and remove any setting that it takes care of.

If you need a setup that the add-on does not support, ignore this rule.


Example
=======

.. code-block:: python

    import scrapy_poet

    ADDONS = {
        scrapy_poet.Addon: 300,
    }


Fix
===

This rule is automatically fixable with the ``--fix`` command-line option:
missing add-ons are enabled in :setting:`ADDONS`, with their recommended
priority, and imported as needed. :setting:`ADDONS` is defined at the end of
the settings module if missing.

The fix requires :setting:`ADDONS` to be either missing or defined as a
dictionary at the top level of the settings module.
