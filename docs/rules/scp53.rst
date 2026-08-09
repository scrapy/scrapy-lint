.. _scp53:

=============================
SCP53: Unsupported injectable
=============================

What it does
============

Reports uses of web-poet page inputs that cannot be injected with the
scrapy-poet version frozen in your :ref:`project requirements <requirements>`.

It also reports the version in which support for the page input was added, in
case you want to consider upgrading.


Why is this bad?
================

Declaring a dependency that no provider can build makes scrapy-poet raise
``NonProvidableError`` at run time.

To fix this, upgrade scrapy-poet to at least the reported version.


Example
=======

With the following :file:`requirements.txt`:

.. code-block:: text

    scrapy-poet==0.14.0

.. code-block:: python

    from web_poet import Stats, WebPage


    class MyPage(WebPage):
        stats: Stats
