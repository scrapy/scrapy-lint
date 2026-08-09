.. _cloud:

============
Scrapy Cloud
============

The ``cloud`` subcommand checks the projects declared in the ``projects`` key
of the :file:`scrapinghub.yml` :ref:`shub configuration file
<shub:configuration>` against `Scrapy Cloud <https://www.zyte.com/scrapy-cloud/>`_::

    pip install scrapy-lint[scrapy-cloud]
    scrapy-lint cloud

It talks to the Scrapy Cloud API, so it is slow, it needs credentials, and its
output can change without a commit. It uses the same API key as :ref:`shub
<shub:configuration>`.

It reports :ref:`SCP47`, and the setting name rules (:ref:`SCP27`,
:ref:`SCP28`, :ref:`SCP29`, :ref:`SCP30`, :ref:`SCP31`, :ref:`SCP33` and
:ref:`SCP46`) for the Scrapy settings defined for each project in Scrapy
Cloud. Every issue is reported at the line of the corresponding
:file:`scrapinghub.yml` project entry, and :ref:`ignore` and
:ref:`per-file-ignores` apply as usual.
