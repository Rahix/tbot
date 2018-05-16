.. TBot

TBot Module
===========

TBot
----

.. autoclass:: tbot.TBot
   :members:

Machines
--------

Machine base class
^^^^^^^^^^^^^^^^^^
.. autoclass:: tbot.machine.machine.Machine
   :members:

Board machine base class
^^^^^^^^^^^^^^^^^^^^^^^^
.. autoclass:: tbot.machine.board.MachineBoard
   :members:
   :inherited-members:

Labhost machine without environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. autoclass:: tbot.machine.lab_noenv.MachineLabNoEnv
   :members:
   :inherited-members:

Labhost machine with environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. autoclass:: tbot.machine.lab_env.MachineLabEnv
   :members:
   :inherited-members:

Board machine for U-Boot interaction
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. autoclass:: tbot.machine.board_uboot.MachineBoardUBoot
   :members:
   :inherited-members:

Board machine for Linux interaction
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. autoclass:: tbot.machine.board_linux.MachineBoardLinux
   :members:
   :inherited-members:

Dummy board machine
^^^^^^^^^^^^^^^^^^^
.. autoclass:: tbot.machine.board_dummy.MachineBoardDummy
   :members:
   :inherited-members:

Utils
-----

.. automodule:: tbot.config
   :members:

.. automodule:: tbot.log
   :members:

.. automodule:: tbot.log_events
   :members:

.. automodule:: tbot.testcase_collector
   :members:

.. automodule:: tbot.machine.shell_utils
   :members:

Machine Manager
^^^^^^^^^^^^^^^

.. autoclass:: tbot.machine.machine.MachineManager
   :members:
   :inherited-members:
