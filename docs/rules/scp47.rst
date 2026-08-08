.. _scp47:

==============================
SCP47: Scrapy version mismatch
==============================

What it does
============

Finds out if the Scrapy version frozen in your :ref:`requirements file
<requirements>` is a different feature version than the one that the ``stack``
of your ``scrapinghub.yml`` :ref:`shub configuration file <shub:configuration>`
comes with.

Only the feature version is compared, i.e. ``2.13`` in ``2.13.3``, so a
different patch version, such as one that :ref:`implements security fixes
<scp15>`, is not reported.

A Scrapy version newer than the one of the newest stack is not reported either,
since using the newest stack is the only way to use a Scrapy release for which
no stack exists yet.


Why is this bad?
================

Scrapy Cloud stacks are named after the Scrapy version they come with, and the
rest of their packages, as well as their Python version, are chosen to work
with it. When you freeze a different Scrapy version, it replaces the one of the
stack, and you get an environment that no one has tested.

Usually the mismatch means that the stack is the outdated part, e.g. you
upgraded Scrapy in your requirements file and forgot about the stack.


Example
=======

With ``scrapy==2.11.2`` in your requirements file:

.. code-block:: yaml

    stack: scrapy:2.13-20250714

Either upgrade the requirement to Scrapy 2.13, or use the matching stack:

.. code-block:: yaml

    stack: scrapy:2.11-20241022
