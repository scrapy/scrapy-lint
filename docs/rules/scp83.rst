.. _scp83:

====================
SCP83: Unused ignore
====================

What it does
============

Reports :ref:`ignore comments <ignore-comments>` that do not suppress an issue,
including individual unused rule codes in comments that suppress other issues.

SCP83 is only reported for Python files and the
:ref:`requirements file <requirements-file>`.


Why is this bad?
================

Unused ignore comments make it harder to tell which exceptions a project still
needs. They can remain after the underlying code or lint configuration changes.


How to fix it
=============

Remove the ignore comment, or remove only the unused rule codes that SCP83
names.


Example
=======

This ignore comment does not suppress an issue:

.. code-block:: python

    allowed_domains = ["toscrape.com"]  # scrapy-lint: ignore[SCP02]

Use instead:

.. code-block:: python

    allowed_domains = ["toscrape.com"]
