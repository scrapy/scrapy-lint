.. _scp50:

======================
SCP50: Discouraged API
======================

What it does
============

Reports uses of an API that is not deprecated yet in the package versions
frozen in your project requirements, but that you can already stop using, and
reports the package and version in which it becomes deprecated.

This is the case when the replacement already exists in the version you use, or
when there is no replacement.

Uses of the same APIs are reported as a :ref:`deprecated API <scp47>` from
their deprecation version on, so that you can silence this rule and still get
the issues that match a run-time deprecation warning.


Why is this bad?
================

Nothing breaks yet, but the migration is already possible, and doing it now
means the next upgrade of the corresponding package neither floods your logs
with deprecation warnings nor requires code changes.


Example
=======

.. code-block:: python

    from scrapy.commands import ScrapyCommand


    class Command(ScrapyCommand):
        def help(self):
            return "Long description of my command"

Use instead:

.. code-block:: python

    from scrapy.commands import ScrapyCommand


    class Command(ScrapyCommand):
        def long_desc(self):
            return "Long description of my command"
