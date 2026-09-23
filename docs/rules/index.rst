.. _rules:

=====
Rules
=====

.. _version-ranges:

Package versions
================

Rules that depend on the version of a package read the version specifiers of
its requirement in your :ref:`requirements file <requirements-file>`, and
report an issue that applies to any version of the declared range.

The lowest version of the range decides whether something does not exist yet,
and the highest version decides whether something is deprecated or removed.
Since a requirement with no upper bound covers every future version, and one
with no lower bound makes no claim of support for old versions, ``scrapy`` on
its own gets deprecations and removals reported, but nothing reported as
missing.

Requirements that only apply under an environment marker are ignored, as they
do not constrain every installation of your project.

.. toctree::
    :maxdepth: 1
    :glob:

    scp*
