.. _scp29:

============================
SCP29: Setting needs upgrade
============================

What it does
============

Reports setting names that do not exist for the lowest package
:ref:`versions your project requirements allow <version-ranges>` but do exist
in higher versions of those packages.

It also reports the package and version in which the setting was introduced, in
case you want to consider upgrading.

Why is this bad?
================

Settings added in newer versions of a package will not work in older versions,
and instead be silently ignored.

To fix this, upgrade the relevant package to at least the version that
introduced the setting.
