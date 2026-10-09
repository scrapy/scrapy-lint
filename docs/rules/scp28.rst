.. _scp28:

=========================
SCP28: Deprecated setting
=========================

What it does
============

Reports setting names that are deprecated for the package versions frozen in
your project requirements.

It also reports the package and version in which the setting was deprecated, so
that you can check the corresponging release notes for sunset guidance.

Sometimes sunset guidance is also provided in the error message.


Why is this bad?
================

Deprecated settings will stop working in future versions of the corresponging
package.

If you do not follow sunset guidance now to migrate or remove the deprecated
setting, the next time you upgrade the corresponding package your project could
break or misbehave.


Fix
===

This rule is automatically fixable with the ``--fix`` command-line option for
settings that were renamed, i.e. that have a replacement taking the same
value: the setting name is renamed, and its value left as is.

It is also fixable for settings whose replacement takes a different value,
such as ``RANDOMIZE_DOWNLOAD_DELAY`` and ``DOWNLOADER_CLIENT_TLS_METHOD``,
when the setting is assigned a literal value in a settings module or in a
dict: the setting is replaced by the settings that express its value, or
removed when its value is what the replacement settings default to.
