.. _scp49:

========================
SCP49: Deprecated import
========================

What it does
============

Reports imports of modules and objects that are deprecated for the package
versions frozen in your project requirements.

It also reports the package and version in which the import was deprecated, so
that you can check the corresponding release notes for sunset guidance.

Sometimes sunset guidance is also provided in the error message.


Why is this bad?
================

Deprecated imports will stop working in future versions of the corresponding
package.

If you do not follow sunset guidance now to migrate or remove the deprecated
import, the next time you upgrade the corresponding package your project could
break.


Fix
===

This rule is automatically fixable with the ``--fix`` command-line option when
the deprecated import has a drop-in replacement under the same name, and every
name of the import statement moves to the same module:

.. code-block:: python

    from scrapy.utils.url import canonicalize_url

becomes:

.. code-block:: python

    from w3lib.url import canonicalize_url
