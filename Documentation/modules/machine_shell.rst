.. py:module:: tbot.machine.shell

``tbot.machine.shell``
======================
Shells are one of the three parts of a machine:  The shell defines the methods
to interact with the machine.  For Linux, the shell will usually be
:py:class:`tbot.machine.linux.Bash`, a shell implementation for interacting
with *bash*.

tbot does not impose any restrictions on how a shell interface is supposed to
look like.  It does make sense to keep it close to existing implementations
though, as long as that is feasible.  Look at the
:py:class:`~tbot.machine.linux.LinuxShell` class for inspiration.

All shells inherit from :py:class:`tbot.machine.shell.Shell`, the base-class
for shells.  For very bare-bones usecases, tbot provides the
:py:class:`~tbot.machine.shell.RawShell` class.

Interactive Access
------------------
A lot of shells have an ``.interactive()`` method which allows accessing the
machine's console directly.  This works similar to a terminal-emulator like
picocom or screen.  The default testcases ``interactive_lab``,
``interactive_board``, ``interactive_uboot``, and ``interactive_linux`` are
using this mechanism, for example.

Base-Class
----------
.. autoclass:: tbot.machine.shell.Shell
   :members:
   :private-members:

Raw-Shell
---------
.. autoclass:: tbot.machine.shell.RawShell
   :members:
