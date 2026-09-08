.. _scp47:

=====================
SCP47: Deprecated API
=====================

What it does
============

Reports uses of an API that is deprecated in the package versions frozen in
your project requirements.

It also reports the package and version in which the API was deprecated, so
that you can check the corresponding release notes for sunset guidance.

Sometimes sunset guidance is also provided in the error message.

Where migrating is already possible in lower versions, uses are reported as a
:ref:`discouraged API <scp50>` until the deprecation version.


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
