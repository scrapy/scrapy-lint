.. _scp48:

============================
SCP48: Stack Python mismatch
============================

What it does
============

Finds out if the Python version of a ``stack`` of your :file:`scrapinghub.yml`
:ref:`shub configuration file <shub:configuration>` does not match the
:ref:`Python version that your project declares <scp49>`.


Why is this bad?
================

Your code runs on the Python version of the stack. If that is not the Python
version that you develop and test on, your project may break once deployed,
even though it works locally and passes your tests.

The Python version of a stack is part of its image, while the packages that it
comes with can be replaced through your :ref:`requirements file <requirements>`.
So declaring the Python version of your stack is usually a much smaller change
than moving to a stack built on the Python version you declare, which comes
with a different set of packages.


Example
=======

Given a project deployed on a stack that runs Python 3.11:

.. code-block:: yaml

    stack: scrapy:2.12-20241202

And a :file:`.python-version` file that declares a different Python version:

.. code-block:: text

    3.12

Instead use:

.. code-block:: text

    3.11
