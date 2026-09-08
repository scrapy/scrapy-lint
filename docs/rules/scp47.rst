.. _scp47:

===========================
SCP47: Outdated requirement
===========================

What it does
============

Finds out if your :ref:`requirements file <requirements>` contains a frozen
[#f1]_ version of Scrapy that was released more than a year before the latest
Scrapy release.

.. [#f1] This rule only fires for frozen versions (using ``==``). Non-frozen
    version specifications like ``scrapy>=2.13.2`` or ``scrapy~=2.13`` are
    ignored.


Why is this bad?
================

`Scrapy keeps deprecated features working for at least 1 year
<https://docs.scrapy.org/en/latest/versioning.html#deprecation-policy>`_. Once
you fall behind that window, features that were deprecated in the version you
use may already be gone from the latest version, so upgrading stops being a
matter of reviewing backward-incompatible changes only.

When you upgrade, read the `release notes
<https://docs.scrapy.org/en/latest/news.html>`_ of every version in between,
and mind their deprecation removals as much as their backward-incompatible
changes.


Example
=======

.. code-block:: text

    scrapy==2.13.2

Instead use:

.. code-block:: text

    scrapy==2.17.0
