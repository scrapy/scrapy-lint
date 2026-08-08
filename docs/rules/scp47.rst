.. _scp47:

=============================
SCP47: Unsorted priority dict
=============================

What it does
============

Finds :ref:`component priority dictionaries <component-priority-dictionaries>`
whose entries are not written in priority order, with disabled components
(``None``) first.


Why is this bad?
================

Components run in priority order, but the order of the entries is what a reader
sees, so entries in a different order suggest a component order that does not
happen.


Example
=======

.. code-block:: python

    DOWNLOADER_MIDDLEWARES = {
        "myproject.middlewares.Late": 900,
        "myproject.middlewares.Early": 100,
    }

Use instead:

.. code-block:: python

    DOWNLOADER_MIDDLEWARES = {
        "myproject.middlewares.Early": 100,
        "myproject.middlewares.Late": 900,
    }


Fix
===

This rule is automatically fixable with the ``--fix`` command-line option:
entries are rewritten in priority order.

Dictionaries containing a comment are reported but not rewritten, since a
comment would stay in place while the entry it documents moves elsewhere.
