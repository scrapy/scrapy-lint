.. _scp44:

=======================
SCP44: Session rotation
=======================

What it does
============

Reports a setting module (e.g. ``settings.py``) that enables
:ref:`scrapy-zyte-api sessions <session>` with a :ref:`session pool
<pool-size>` larger than 1, be it through
:setting:`ZYTE_API_SESSION_POOL_SIZE`, which defaults to 8, or through the
``size`` key of :setting:`ZYTE_API_SESSION_POOLS`.


Why is this bad?
================

Every session in a pool is a separate identity from the point of view of the
target website. A pool of 8 sessions makes a single crawl look like 8 different
visitors, each of which sends requests 8 times less often than you actually do.

Website owners should be able to tell that your requests are all yours, so that
they can throttle you or block you if they want to.

A larger pool is the feature working as intended: pools exist to extend the
lifetime of sessions on websites that push back. This rule asks you to give
that up in exchange for being attributable; :ref:`silence it <ignore>` if that
is not a trade-off you want to make.


Example
=======

.. code-block:: python

    ZYTE_API_SESSION_ENABLED = True

Instead use:

.. code-block:: python

    ZYTE_API_SESSION_ENABLED = True
    ZYTE_API_SESSION_POOL_SIZE = 1
