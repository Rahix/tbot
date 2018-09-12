``tbot.machine.linux`` Module
=============================

``tbot.machine.linux``
----------------------
.. autoclass:: tbot.machine.linux.LinuxMachine
    :members:

.. autoclass:: tbot.machine.linux.Path
    :members:

.. autoclass:: tbot.machine.linux.Workdir
    :members:

Command Specials
^^^^^^^^^^^^^^^^
.. autoclass:: tbot.machine.linux.Env
.. py:data:: tbot.machine.linux.Pipe

    Special character for the ``|`` pipe to send command output
    to another command

    **Example**::

        m.exec0("dmesg", linux.Pipe, "grep", "usb0")

.. py:data:: tbot.machine.linux.Then

    Special character for the ``;`` separator to run multiple commands

    **Example**::

        m.exec0("sleep", "1", linux.Then, "date")

.. py:data:: tbot.machine.linux.Background

    Special character for the ``&`` separator to run a command in the background

    **Example**::

        m.exec0("daemon", linux.Backround)

.. py:data:: tbot.machine.linux.OrElse

    Special character for the ``||`` separator to run a command if the
    first one failed

    **Example**::

        m.exec0("test", "-d", "/foo/bar", linux.OrElse, "mkdir", "-p", "/foo/bar")

.. py:data:: tbot.machine.linux.AndThen

    Special character for the ``&&`` separator to run a command if the
    first one succeeded

    **Example**::

        m.exec0("test", "-d", ".git", linux.AndThen, "git", "describe", "--tags")

.. autoclass:: tbot.machine.linux.Raw

Implementations
^^^^^^^^^^^^^^^
.. autoclass:: tbot.machine.linux.LabHost
    :members:

.. autoclass:: tbot.machine.linux.BuildMachine
    :members:

.. autoclass:: tbot.machine.linux.SSHMachine
    :members:


``tbot.machine.linux.auth``
---------------------------
.. automodule:: tbot.machine.linux.auth
    :members:


``tbot.machine.linux.lab``
--------------------------
.. autoclass:: tbot.machine.linux.lab.LocalLabHost
    :members:

.. autoclass:: tbot.machine.linux.lab.SSHLabHost
    :members:


``tbot.machine.linux.build``
----------------------------
.. autoclass:: tbot.machine.linux.build.Toolchain
    :members:

.. autoclass:: tbot.machine.linux.build.EnvScriptToolchain
    :members:


``tbot.machine.linux.shell``
----------------------------
.. autoclass:: tbot.machine.linux.shell.Shell
    :members:

.. autoclass:: tbot.machine.linux.shell.Bash
    :members:

.. autoclass:: tbot.machine.linux.shell.Ash
    :members:
