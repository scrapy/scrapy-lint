.. _scp30:

======================
SCP30: Removed setting
======================

What it does
============

Reports setting names that have been removed from any of the package
:ref:`versions your project requirements allow <version-ranges>` but do exist
in lower versions of those packages.

It also reports the package that defined the setting, the version in which the
setting was deprecated, and the version in which it was removed, so that you
can check the corresponging release notes for sunset guidance.

Sometimes sunset guidance is also provided in the error message.

Why is this bad?
================

Removed settings have stopped working the way they used to, and instead are
silently ignored.
