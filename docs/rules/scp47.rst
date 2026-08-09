.. _scp47:

==========================
SCP47: Unreachable project
==========================

What it does
============

Finds projects declared in the ``projects`` key of the :file:`scrapinghub.yml`
:ref:`shub configuration file <shub:configuration>` that Scrapy Cloud does not
report as available to the API key in use.

Only reported by :ref:`scrapy-lint cloud <cloud>`.


Why is this bad?
================

The project has been removed, its ID is wrong, or the API key in use does not
have access to it. Deployments and scheduled jobs targeting it will fail.


Examples
========

.. code-block:: yaml

    projects:
      default: 12345

If ``12345`` does not exist, replace it with the ID that the Scrapy Cloud
dashboard shows for the project, or drop the entry.
