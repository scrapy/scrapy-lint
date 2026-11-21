.. _scp74:

=====================
SCP74: Deprecated API
=====================

What it does
============

Reports uses of an API that is deprecated in any of the package
:ref:`versions your project requirements allow <version-ranges>`.

It also reports the package and version in which the API was deprecated, so
that you can check the corresponding release notes for sunset guidance.

Sometimes sunset guidance is also provided in the error message.

Where migrating is already possible in lower versions, uses are reported as a
:ref:`discouraged API <scp77>` until the deprecation version.


Why is this bad?
================

Deprecated APIs will stop working in future versions of the corresponding
package.

If you do not follow sunset guidance now to migrate away from the deprecated
API, the next time you upgrade the corresponding package your project could
break or misbehave.


Example
=======

.. code-block:: python

    from scrapy.exporters import PythonItemExporter

    exporter = PythonItemExporter(binary=True)

Use instead:

.. code-block:: python

    from scrapy.exporters import PythonItemExporter

    exporter = PythonItemExporter(binary=False)


Fix
===

This rule is automatically fixable with the ``--fix`` command-line option for
calls to ``Spider.log()``, which become calls to the ``Spider.logger`` method
of their logging level, e.g. ``self.logger.info()`` for ``logging.INFO``.
