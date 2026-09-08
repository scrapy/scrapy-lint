.. _scp49:

========================
SCP49: Python not frozen
========================

What it does
============

Finds out if the Python version that your project declares does not name a
single Python version series, e.g. a version range.

Leaving the patch version out, e.g. ``3.12``, is fine: Python patch releases
only carry bug fixes, and the rare fixes that break backward compatibility
reach every supported series at once, so pinning the patch version protects
you from nothing.

The declaration comes from the :file:`.python-version` file, or from the
``requires-python`` key of your :file:`pyproject.toml` file.


Why is this bad?
================

A Scrapy project is an application, not a library, so every developer and every
environment that runs it should run it on the same Python, in the same way that
they should install the same :ref:`frozen requirements <scp13>`.

Python versions that differ between environments introduce bugs that only
happen for some developers, or only in production, and that are hard to
reproduce. Every Python series has its own syntax, its own standard library and
its own wheels.


Example
=======

.. code-block:: toml

    [project]
    requires-python = ">=3.12"

Instead use:

.. code-block:: toml

    [project]
    requires-python = "==3.12.*"
