.. _scp47:

=========================
SCP47: End-of-life Python
=========================

What it does
============

Finds out if your project declares, or runs on, a version of Python that has
reached its `end of life <https://devguide.python.org/versions/>`_.

The Python version comes from the :ref:`declaration of your project <scp49>`
and from the ``stack`` values of your :file:`scrapinghub.yml` :ref:`shub
configuration file <shub:configuration>`.


Why is this bad?
================

Once a version of Python reaches its end of life, it stops receiving security
fixes, and the packages of the Scrapy ecosystem stop supporting it, so you no
longer get their new features and bug fixes either.


Example
=======

.. code-block:: text

    3.9.23

Instead use:

.. code-block:: text

    3.12.11
