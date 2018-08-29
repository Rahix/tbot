``tbot.machine.linux`` Module
=============================

``tbot.machine.linux``
----------------------
.. automodule:: tbot.machine.linux
    :members:
    :undoc-members:

.. py:data:: tbot.machine.linux.Pipe

    Special character for the ``|`` pipe to send command output
    to another command

    **Example**::

        m.exec0("dmesg", linux.Pipe, "grep", "usb0")

.. automodule:: tbot.machine.linux.machine
.. automodule:: tbot.machine.linux.path
.. automodule:: tbot.machine.linux.special
.. automodule:: tbot.machine.linux.lab.machine


``tbot.machine.linux.auth``
---------------------------
.. automodule:: tbot.machine.linux.auth
    :members:


``tbot.machine.linux.lab``
--------------------------
.. automodule:: tbot.machine.linux.lab
    :members:
    :undoc-members:

.. automodule:: tbot.machine.linux.lab.local
.. automodule:: tbot.machine.linux.lab.ssh


``tbot.machine.linux.build``
----------------------------
.. automodule:: tbot.machine.linux.build
    :members:

.. automodule:: tbot.machine.linux.build.machine
.. automodule:: tbot.machine.linux.build.toolchain


``tbot.machine.linux.ssh``
--------------------------
.. automodule:: tbot.machine.linux.ssh
    :members:

.. automodule:: tbot.machine.linux.ssh.machine


``tbot.machine.linux.shell``
----------------------------
.. automodule:: tbot.machine.linux.shell
    :members:

.. automodule:: tbot.machine.linux.shell.shell
.. automodule:: tbot.machine.linux.shell.bash
.. automodule:: tbot.machine.linux.shell.ash
