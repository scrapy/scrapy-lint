.. _scp53:

=======================
SCP53: Hardcoded secret
=======================

What it does
============

Reports a credential written as a literal string, either as the value of a
setting known to hold a secret, such as :setting:`AWS_SECRET_ACCESS_KEY` or
:setting:`ZYTE_API_KEY`, or in the ``apikeys`` key of the
:file:`scrapinghub.yml` :ref:`shub configuration file <shub:configuration>`.


Why is this bad?
================

A credential in your code base is a credential in your version control history,
readable by anyone with access to the repository, and by anyone who gets access
later. Rewriting history does not help: mirrors, forks, clones and backups keep
the old commits.

Credentials also belong to a person or an environment, not to a project.
Hardcoding one forces everyone to share it, and makes it impossible to use
different credentials for development and production.


Example
=======

.. code-block:: python

    ZYTE_API_KEY = "a0e2b7cee1e04b9f9d1b3f2f9d5a7c31"

Read the credential from the environment instead:

.. code-block:: python

    import os

    ZYTE_API_KEY = os.environ["ZYTE_API_KEY"]

Some components read their credential from the environment on their own, in
which case you can drop the setting altogether. :doc:`scrapy-zyte-api
<scrapy-zyte-api:index>` reads ``ZYTE_API_KEY`` from the environment, and
``shub`` reads ``SHUB_APIKEY``, so instead of:

.. code-block:: yaml

    apikeys:
      default: a0e2b7cee1e04b9f9d1b3f2f9d5a7c31

remove the ``apikeys`` key and export ``SHUB_APIKEY``.

To set those environment variables automatically as you enter your project
directory, use `direnv <https://direnv.net/>`_ and define them in an
:file:`.envrc` file that you keep out of version control.

Once a credential has been committed, rotate it. Removing it from the code
does not make the leaked value safe to keep using.

This rule only knows about settings that always hold a secret. To catch
credentials anywhere else in your code base, combine it with a dedicated secret
scanner such as `gitleaks <https://github.com/gitleaks/gitleaks>`_ or
`detect-secrets <https://github.com/Yelp/detect-secrets>`_, both available as
pre-commit hooks.
