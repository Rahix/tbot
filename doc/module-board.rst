``tbot.machine.board`` Module
=============================
.. automodule:: tbot.machine.board.board
.. autoclass:: tbot.machine.board.Board
    :members:

.. automodule:: tbot.machine.board.machine
.. autoclass:: tbot.machine.board.BoardMachine
    :members:


U-Boot
------
.. automodule:: tbot.machine.board.uboot
.. autoclass:: tbot.machine.board.UBootMachine
    :members:


Special Characters
^^^^^^^^^^^^^^^^^^
.. automodule:: tbot.machine.board.special

.. autoclass:: tbot.machine.board.Env
    :members:

.. autoclass:: tbot.machine.board.F
    :members:

.. autoclass:: tbot.machine.board.Raw
    :members:

.. py:data:: tbot.machine.board.Then

    Special character for the ``;`` separator to run multiple commands

    **Example**::

        m.exec0("if", "true", board.Then, "then", "echo", "Hallo", board.Then, "fi")


Linux
-----
.. automodule:: tbot.machine.board.linux

.. autoclass:: tbot.machine.board.LinuxWithUBootMachine
    :members:

.. autoclass:: tbot.machine.board.LinuxStandaloneMachine
    :members:
