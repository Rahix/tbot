.. TBot

TBot Module
===========

TBot
----

.. autoclass:: tbot.TBot
   :members:

Machines
--------

Machine Base Class
^^^^^^^^^^^^^^^^^^
.. autoclass:: tbot.machine.machine.Machine
   :members:

Board Machine Base Class
^^^^^^^^^^^^^^^^^^^^^^^^
.. autoclass:: tbot.machine.board.MachineBoard
   :members:
   :inherited-members:

Labhost Machine Without Environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. autoclass:: tbot.machine.lab_noenv.MachineLabNoEnv
   :members:
   :inherited-members:

Labhost Machine With Environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. autoclass:: tbot.machine.lab_env.MachineLabEnv
   :members:
   :inherited-members:

Buildhost Machine
^^^^^^^^^^^^^^^^^
.. autoclass:: tbot.machine.build.MachineBuild
   :members:
   :inherited-members:

Board Machine For U-Boot Interaction
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. autoclass:: tbot.machine.board_uboot.MachineBoardUBoot
   :members:
   :inherited-members:

Board Machine For Linux Interaction
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. autoclass:: tbot.machine.board_linux.MachineBoardLinux
   :members:
   :inherited-members:

Dummy Board Machine
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
