.. _scp49:

===============================
SCP49: Incompatible requirement
===============================

What it does
============

Finds out if your :ref:`requirements file <requirements-file>` freezes [#f1]_ a
package version that is too low for another frozen package version.

.. [#f1] This rule only fires for frozen versions (using ``==``). Non-frozen
    version specifications like ``scrapy>=2.11.0`` or ``scrapy~=2.11`` are
    ignored.


Why is this bad?
================

Your project breaks at run time, often in a way that does not point at the
requirement that needs an upgrade. For example, ``scrapinghub-entrypoint-scrapy``
before 0.14.1 uses the binary export mode of
:class:`~scrapy.exporters.PythonItemExporter`, removed in Scrapy 2.11.0, so on
Scrapy 2.11.0 and higher it fails with ``TypeError: Unexpected options:
binary``.


Example
=======

.. code-block:: text

    scrapinghub-entrypoint-scrapy==0.13.0
    scrapy==2.13.2

Use instead:

.. code-block:: text

    scrapinghub-entrypoint-scrapy==0.14.1
    scrapy==2.13.2
