.. _scp47:

=================================
SCP47: Stack requirement conflict
=================================

What it does
============

Finds out if the packages of your :ref:`requirements file <requirements>` can be
installed on top of the frozen ``stack`` of your ``scrapinghub.yml``
:ref:`shub configuration file <shub:configuration>` without breaking any of the
packages that the stack comes with.

The check uses uv_ to resolve the package list of your stack together with your
requirements, so it reports nothing where uv is unavailable. Package lists ship
with scrapy-lint, and those of stacks released later are downloaded and cached
on first use.

In continuous integration, persist the uv cache directory to keep the check
fast.

.. _uv: https://docs.astral.sh/uv/


Why is this bad?
================

When you deploy to Scrapy Cloud, your requirements are installed on top of a
stack that already comes with a set of packages. Your versions replace those of
the stack, while the stack packages that your requirements file does not mention
stay as they are.

If one of those packages does not support a version that you install, it breaks
at run time, when it imports or calls something that is no longer there.


Example
=======

Given a stack that comes with ``spidermon==1.20.0``, which requires
``scrapy>=2.0``:

.. code-block:: text

    scrapy==1.8.0

Use instead:

.. code-block:: text

    scrapy==2.13.3
