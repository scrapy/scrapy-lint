===========
scrapy-lint
===========

|version| |python_version| |ci| |codecov|

.. |version| image:: https://img.shields.io/pypi/v/scrapy-lint.svg
   :target: https://pypi.org/pypi/scrapy-lint
   :alt: PyPI version

.. |python_version| image:: https://img.shields.io/pypi/pyversions/scrapy-lint.svg
   :target: https://pypi.org/pypi/scrapy-lint
   :alt: Supported Python versions

.. |ci| image:: https://github.com/scrapy/scrapy-lint/workflows/CI/badge.svg
   :target: https://github.com/scrapy/scrapy-lint/actions?query=workflow%3ACI
   :alt: CI

.. |codecov| image:: https://codecov.io/gh/scrapy/scrapy-lint/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/scrapy/scrapy-lint
    :alt: Coverage

.. readme-start

**scrapy-lint** is a linter for `Scrapy <https://scrapy.org/>`_ projects.

To install::

    pip install scrapy-lint

To run::

    scrapy-lint

Some issues can be fixed automatically. Such issues are marked with ``[*]`` in
the output, and you can apply their fixes with the ``--fix`` option::

    scrapy-lint --fix

There is also a separate subcommand that checks your project against `Scrapy
Cloud <https://www.zyte.com/scrapy-cloud/>`_::

    pip install scrapy-lint[scrapy-cloud]
    scrapy-lint cloud

To use with `pre-commit <https://pre-commit.com/>`__, add the following to your
``.pre-commit-config.yaml``:

.. code-block:: yaml

    - repo: https://github.com/scrapy/scrapy-lint
      rev: v0.1.1
      hooks:
      - id: scrapy-lint

Can be combined with `ruff <https://docs.astral.sh/ruff/>`_,
`mypy <https://mypy.readthedocs.io/en/stable/>`_,
`pylint <https://pylint.readthedocs.io/en/stable/>`_ and
`flake8-requirements <https://pypi.org/project/flake8-requirements/>`_.

.. readme-end

Documentation
=============

See the documentation_ for more.

.. _documentation: https://scrapy-lint.readthedocs.io/en/latest/
