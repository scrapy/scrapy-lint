.. _scp52:

========================
SCP52: Deprecated method
========================

What it does
============

Reports calls to deprecated methods.

It also reports the package and version in which the method was deprecated, so
that you can check the corresponding release notes for sunset guidance.

Sometimes sunset guidance is also provided in the error message.


Why is this bad?
================

Deprecated methods will stop working in future versions of the corresponding
package.

If you do not follow sunset guidance now to migrate away from the deprecated
method, the next time you upgrade the corresponding package your project could
break or misbehave.
