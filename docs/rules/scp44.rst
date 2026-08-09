.. _scp44:

=============================
SCP44: Improper setting value
=============================

What it does
============

Reports setting values that Scrapy accepts but that are a poor way to express
the intended value:

-   A dict assigned to a setting that is read as a list.

-   A value other than ``True`` or ``False`` assigned to a boolean setting.

-   An integer assigned to :setting:`LOG_LEVEL`.

-   A JSON string assigned to a setting that is read as a dict or a list.


Why is this bad?
================

Such values are harder to read, and often a symptom of a mistake.

A dict assigned to a list setting is read as the list of its keys, which is
rarely what is intended.

A JSON string is not checked by this tool beyond being valid JSON, so mistakes
in its contents go unreported.


Example
=======

.. code-block:: python
    :caption: :file:`settings.py`

    ADDONS = '{"myproject.addons.Addon": 100}'
    LOG_LEVEL = 10
    ROBOTSTXT_OBEY = "1"
    SPIDER_MODULES = {"myproject.spiders": None}

Instead use:

.. code-block:: python
    :caption: :file:`settings.py`

    import logging

    import myproject.addons

    ADDONS = {myproject.addons.Addon: 100}
    LOG_LEVEL = logging.DEBUG
    ROBOTSTXT_OBEY = True
    SPIDER_MODULES = ["myproject.spiders"]
