``tbot.machine.linux`` Module
=============================

``tbot.machine.linux``
----------------------
.. autoclass:: tbot.machine.linux.LinuxMachine
    :members:

.. autoclass:: tbot.machine.linux.Path
    :members:

Command Specials
^^^^^^^^^^^^^^^^
.. autoclass:: tbot.machine.linux.Env
.. py:data:: tbot.machine.linux.Pipe

    Special character for the ``|`` pipe to send command output
    to another command

    **Example**::

        m.exec0("dmesg", linux.Pipe, "grep", "usb0")

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
