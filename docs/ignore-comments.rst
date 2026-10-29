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

For a line that cannot end in a comment, because it is inside a multi-line
string or ends in a backslash, put the comment at the end of the next line that
can:

.. blacken-docs:off

.. code-block:: python

    allowed_domains = ["https://toscrape.com", """
    """]  # scrapy-lint: ignore[SCP02]

.. blacken-docs:on

Ignore comments also work on :file:`requirements.txt`, :file:`pyproject.toml`
and :file:`scrapinghub.yml`:

.. code-block:: yaml

    stack: scrapy:2.12  # scrapy-lint: ignore[SCP20]

In a :file:`Dockerfile` or :file:`.python-version` file, put the comment on its
own line right before the line to ignore. In a :file:`Dockerfile`, it covers
every line of the instruction that follows it:

.. code-block:: dockerfile

    # scrapy-lint: ignore[SCP20]
    FROM scrapinghub/scrapinghub-stack-scrapy:2.12

Some rules report issues about a file as a whole, such as :ref:`SCP13` or
:ref:`SCP18`, and point at its first line. Use :ref:`per-file-ignores` for
those.

Adding ignore comments
======================

To add ignore comments for every issue found, e.g. when you start using
scrapy-lint on an existing project, use the ``--add-ignore`` option::

    scrapy-lint --add-ignore

Issues about a file as a whole are ignored with :ref:`per-file-ignores`
instead, added to :file:`pyproject.toml`.
