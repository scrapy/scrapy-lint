.. _ignore-comments:

===============
Ignore comments
===============

To ignore an issue on a specific line, add a comment to that line:

.. code-block:: python

    allowed_domains = ["https://toscrape.com"]  # scrapy-lint: ignore[SCP02]

List several :ref:`rules` separated by commas, or omit the brackets to ignore
every rule on that line:

.. code-block:: python

    allowed_domains = ["https://toscrape.com"]  # scrapy-lint: ignore

Ignore comments work on every file that scrapy-lint checks, including
:file:`requirements.txt` and :file:`scrapinghub.yml`:

.. code-block:: yaml

    stack: scrapy:2.12  # scrapy-lint: ignore[SCP20]

Some rules report issues about a file as a whole, such as :ref:`SCP13` or
:ref:`SCP18`, and point at its first line. Use :ref:`per-file-ignores` for
those.
