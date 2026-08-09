.. _scp47:

================================
SCP47: Hidden callback type hint
================================

What it does
============

Finds spider method annotations that use a name imported only for type
checking.

Only reported in projects that declare requirements including scrapy-poet_,
and only in modules using `postponed evaluation of annotations`_.

.. _postponed evaluation of annotations: https://docs.python.org/3/library/__future__.html#id1
.. _scrapy-poet: https://scrapy-poet.readthedocs.io/en/stable/


Why is this bad?
================

scrapy-poet resolves the type hints of every callback at run time, to decide
which dependencies to inject. If a type hint is only imported during type
checking, that resolution fails:

.. code-block:: pytb

    NameError: name 'Response' is not defined

Note that the whole signature is resolved, so any type hint breaks it, not only
those of injected parameters.


Example
=======

.. code-block:: python

    from __future__ import annotations

    from typing import TYPE_CHECKING

    import scrapy

    if TYPE_CHECKING:
        from scrapy.http import Response


    class MySpider(scrapy.Spider):
        name = "myspider"

        def parse(self, response: Response): ...

Use instead:

.. code-block:: python

    from __future__ import annotations

    import scrapy
    from scrapy.http import Response


    class MySpider(scrapy.Spider):
        name = "myspider"

        def parse(self, response: Response): ...

Linters that move imports into a type-checking block, such as `Ruff TC002`_,
report those imports again. Disable them for your spiders and your page
objects, whose type hints are also resolved at run time. For example, for Ruff:

.. code-block:: toml

    [tool.ruff.lint.per-file-ignores]
    "**/pages/*.py" = ["TC001", "TC002", "TC003"]
    "**/spiders/*.py" = ["TC001", "TC002", "TC003"]

.. _Ruff TC002: https://docs.astral.sh/ruff/rules/typing-only-third-party-import/
