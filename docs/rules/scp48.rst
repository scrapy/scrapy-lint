.. _scp48:

==================
SCP48: Removed API
==================

What it does
============

Reports uses of an API that has been removed from the package versions frozen
in your project requirements but does exist in lower versions of those
packages.

It also reports the package that defined the API, the version in which the API
was deprecated, and the version in which it was removed, so that you can check
the corresponding release notes for sunset guidance.


Why is this bad?
================

Removed APIs no longer work. Depending on the API, your project either
misbehaves or raises an exception, such as ``TypeError: Unexpected options:
binary`` for the example below.


Example
=======

.. code-block:: python

    from scrapy.exporters import PythonItemExporter

    exporter = PythonItemExporter(binary=False)

Use instead:

.. code-block:: python

    from scrapy.exporters import PythonItemExporter

    exporter = PythonItemExporter()


Fix
===

This rule is automatically fixable with the ``--fix`` command-line option for
removed parameters that only need to be dropped, like the one above.
