.. py:module:: tbot.machine.linux

``tbot.machine.linux``
======================
This module contains utilities for interacting with linux hosts.  This includes:

- :ref:`linux-shells`
- tbot's own path type: :py:class:`tbot.machine.linux.Path`

.. _linux-shells:

Linux Shells
------------
The base-class :py:class:`tbot.machine.linux.LinuxShell` defines the common
interface all linux-shells should provide.  This interface consists of the
following methods:

- :py:meth:`lnx.escape() <tbot.machine.linux.LinuxShell.escape>` - Escape args
  for the underlying shell.
- :py:meth:`lnx.exec0() <tbot.machine.linux.LinuxShell.exec0>` - Run command
  and ensure it succeeded.
- :py:meth:`lnx.exec() <tbot.machine.linux.LinuxShell.exec>` - Run command and
  return output and return code.
- :py:meth:`lnx.test() <tbot.machine.linux.LinuxShell.test>` - Run command and
  return boolean whether it succeeded.
- :py:meth:`lnx.env() <tbot.machine.linux.LinuxShell.env>` - Get/Set
  environment variables.
- :py:meth:`lnx.subshell() <tbot.machine.linux.LinuxShell.subshell>` - Start a
  subshell environment.
- :py:meth:`lnx.interactive() <tbot.machine.linux.LinuxShell.interactive>` -
  Start an interactive session for this machine.

And the following properties:

- :py:attr:`lnx.username <tbot.machine.linux.LinuxShell.username>` - Current
  user.
- :py:attr:`lnx.fsroot <tbot.machine.linux.LinuxShell.fsroot>` - Path to the
  file-system root (just for convenience).
- :py:attr:`lnx.workdir <tbot.machine.linux.LinuxShell.workdir>` - Path to a
  directory which testcases can store files in.

tbot contains implementations of
this interface for the following shells:

.. autoclass:: tbot.machine.linux.Bash

.. autoclass:: tbot.machine.linux.LinuxShell
   :members:


.. _linux-argtypes:

Argument Types
~~~~~~~~~~~~~~
For a lot of methods defined in :py:class:`~tbot.machine.linux.LinuxShell`, a
special set of types can be given as arguments.  This protects against a lot of
common errors.  The allowed types are:

- :py:class:`str` - Every string argument will be properly quoted so the shell
  picks it up as only one parameter.  Example:

  .. code-block:: python

     lnx.exec0("echo", "Hello World!", "Is this tbot?")

     # Will run:
     #    echo "Hello World!" "Is this tbot?"

- :py:class:`tbot.machine.linux.Path` - tbot's path class keeps track of the
  machine the path is associated with.  This prevents you from accidentally
  using a path from one host on another.  The path class behaves like
  :py:mod:`pathlib` paths, so you can do things like:

  .. code-block:: python

     tftpdir = lnx.fsroot / "var" / "lib" / "tftpboot"
     lnx.exec0("ls", "-1", tftpdir)

     if (tftpdir / "u-boot.bin").is_file():
         tbot.log.message("Binary exists!")

- **"Specials"** - Sometimes you will need special shell-syntax for certain
  operations, for example to redirect output of a command.  For these things,
  tbot provides special "tokens".  The full list can be found in
  :ref:`linux-specials`.  As an example, redirecting to a file works like this:

  .. code-block:: python

     lnx.exec0("dmesg", linux.RedirStdout(lnx.workdir / "kernel.log"))
     # Will run:
     #    dmesg >/tmp/tbot-wd/kernel.log


.. _linux-specials:

Specials
~~~~~~~~
Specials can be used as part of commands to use certain shell-syntaxes.  This
can be used to chain multiple commands or to redirect output.

.. py:data:: AndThen

   Chain commands using ``&&``.

   **Example**:

   .. code-block:: python

      lnx.exec0("sleep", str(10), linux.AndThen, "echo", "Hello!")

.. py:data:: OrElse

   Chain commands using ``||``.

.. py:data:: Then

   Chain commands using ``;``.

.. py:data:: Pipe

   Pipe the output of one command into another:

   .. code-block:: python

      lnx.exec0("dmesg", linux.Pipe, "grep", "usb")

.. py:class:: RedirStdout(file)

   Redirect ``stdout`` (``>...``) to a file.

.. py:class:: RedirStderr(file)

   Redirect ``stderr`` (``2>...``) to a file.

.. py:class:: Raw(str)

   Emits a raw string, bypassing shell quoting/escaping.

   .. warning::

      Only use this if nothing else works!  :py:class:`linux.Raw
      <tbot.machine.linux.Raw>` can quickly lead to hard-to-find bugs.


Paths
-----
.. autoclass:: tbot.machine.linux.Path
   :members:

Workdir
~~~~~~~
.. py:class:: Workdir

   .. automethod:: tbot.machine.linux.Workdir.static
   .. automethod:: tbot.machine.linux.Workdir.athome

Lab-Host
--------
.. autoclass:: tbot.machine.linux.Lab
   :members:

Builder
-------
The :py:class:`~tbot.machine.linux.Builder` mixin allows marking a machine as a build-host.  This
means generic testcases like ``uboot.build`` can use it to automatically build projects.  For this
to work, a build-host needs to specify which toolchains it has installed and where tbot can find
them.

.. autoclass:: tbot.machine.linux.Builder
   :members:

.. py:module:: tbot.machine.linux.build

Toolchains
~~~~~~~~~~
.. autoclass:: tbot.machine.linux.build.Toolchain
   :members:

.. autoclass:: tbot.machine.linux.build.EnvScriptToolchain
   :members:
