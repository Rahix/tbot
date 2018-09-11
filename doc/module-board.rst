``tbot.machine.board`` Module
=============================
.. autoclass:: tbot.machine.board.Board
    :members:

.. autoclass:: tbot.machine.board.BoardMachine
    :members:

.. automodule:: tbot.machine.board.board
.. automodule:: tbot.machine.board.machine

U-Boot
------
.. autoclass:: tbot.machine.board.UBootMachine
    :members:

.. automodule:: tbot.machine.board.uboot

Special Characters
^^^^^^^^^^^^^^^^^^
.. autoclass:: tbot.machine.board.Env
    :members:

.. autoclass:: tbot.machine.board.Raw
    :members:

.. py:data:: tbot.machine.board.Then

    Special character for the ``;`` separator to run multiple commands

    **Example**::

        m.exec0("if", "true", board.Then, "then", "echo", "Hallo", board.Then, "fi")

.. automodule:: tbot.machine.board.special

Linux
-----
.. autoclass:: tbot.machine.board.LinuxWithUBootMachine
    :members:

.. autoclass:: tbot.machine.board.LinuxStandaloneMachine
    :members:

.. automodule:: tbot.machine.board.linux
