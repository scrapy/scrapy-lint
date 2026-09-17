.. _scp36:

============================
SCP36: Invalid setting value
============================

What it does
============

Reports the assigning of a value to a setting that does not support that value.


Why is this bad?
================

Best case scenario, the value is ignored with a warning. Worst case scenario,
the value breaks your code.


Example
=======

.. code-block:: python
    :caption: ``settings.py``

    CONCURRENT_REQUESTS_PER_DOMAIN = "minimum"

Instead, check the settings reference documentation of the corresponding
package (e.g. :ref:`Scrapy settings <topics-settings>`) to see what values are
valid for the setting, and assign a valid value:

.. code-block:: python
    :caption: ``settings.py``

    CONCURRENT_REQUESTS_PER_DOMAIN = 1

Feed URIs are a common source of this issue, because credentials must be
percent-encoded, e.g. with :func:`urllib.parse.quote`, for the rest of the URI
to be parsed as intended:

.. code-block:: python
    :caption: ``settings.py``

    FEEDS = {"ftp://jane:pa%2Fss@ftp.example.com/output.json": {"format": "json"}}
