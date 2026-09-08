.. _scp50:

=====================
SCP50: Removed import
=====================

What it does
============

Reports imports of modules and objects that have been removed from the package
versions frozen in your project requirements but do exist in lower versions of
those packages.

It also reports the package that defined the module or object, the version in
which it was deprecated, and the version in which it was removed, so that you
can check the corresponding release notes for sunset guidance.

Sometimes sunset guidance is also provided in the error message.


Why is this bad?
================

Removed imports raise :exc:`ImportError`.
