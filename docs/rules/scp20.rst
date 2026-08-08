.. _scp20:

=======================
SCP20: Stack not frozen
=======================

What it does
============

Finds ``stack`` values in the :file:`scrapinghub.yml` :ref:`shub configuration
file <shub:configuration>` that do not end with a date suffix in the format
``-YYYYMMDD``.

In projects that :file:`scrapinghub.yml` deploys as a custom image, with
``image: true``, it finds those stack values in the ``FROM`` instructions of
the :file:`Dockerfile` instead.


Why is this bad?
================

When you use a stack *without* a date suffix (like ``scrapy:2.12`` instead of
``scrapy:2.12-20241202``), you're using a floating tag that can change over
time as new versions are published.

Stack values should always be frozen to a specific date to ensure reproducible
deployments.


Where can I find available stack versions?
==========================================

See https://hub.docker.com/r/scrapinghub/scrapinghub-stack-scrapy/tags for
available stack versions and their corresponding date suffixes.


Example
=======

.. code-block:: yaml

    stack: scrapy:2.12

Instead use:

.. code-block:: yaml

    stack: scrapy:2.12-20241202
