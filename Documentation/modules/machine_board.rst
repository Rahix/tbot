.. py:module:: tbot.machine.board

``tbot.machine.board``
======================
This module contains definitions for interacting with embedded hardware.  tbot
models hardware in a 'layered' approach:

- The underlying physical hardware is called a *board*.  The board class
  defines how tbot can connect to the board's console, how to turn power on and
  off, etc.
- Ontop of the board, the software 'layer' is defined.  This might be a U-Boot,
  a Linux directly, or a Linux ontop of a U-Boot.  It could also be something
  completely custom if you implement the relevant
  :py:class:`~tbot.machine.Initializer` s and
  :py:class:`~tbot.machine.shell.Shell` s.

Each of these 'layers' is its own machine.  See the docs for:

- :ref:`board-hardware`
- :ref:`board-software`
- :ref:`board-uboot`
- :ref:`board-linux`

.. _board-hardware:

Board Hardware
--------------
The board-machine should inherit from :py:class:`tbot.machine.board.Board` and
define the pysical access for the hardware.  This means the connector will most
likely be a :py:class:`~tbot.machine.connector.ConsoleConnector` and it might
make use of the :py:class:`tbot.machine.board.PowerControl` initializer to turn
on/off power for the board.

**Example**:

.. code-block:: python

   from tbot.machine import connector, board, linux

   class MyBoard(
       connector.ConsoleConnector,
       board.PowerControl,
       board.Board,
   ):
       # TODO


.. autoclass:: tbot.machine.board.Board
   :members:

Board Initializers
~~~~~~~~~~~~~~~~~~
.. autoclass:: tbot.machine.board.PowerControl
   :members:


.. _board-software:

Board Software
--------------
The 'software layer' machines for a board should not directly use a connector
to connect to the boards console, but instead rely on the generic
:py:class:`tbot.machine.board.Connector` class.  This allows cleanly separating
the hardware and software and thus reusing the software machines with different
hardware.

In practice, these 'software machines' should be defined like this:

.. code-block:: python

   from tbot.machine import board

   class MyBoard(
       ...
       board.Board,
   ):
       # Hardware machine
       ...

   class MyBoardSoftware(
      board.Connector,
      ...
   ):
      # Software machine
      ...


And then used like

.. code-block:: python

   with MyBoard(lh) as b:
      with MyBoardSoftware(b) as bs:
         bs.exec(...)

   # Or, more consise
   with MyBoard(lh) as b, MyBoardSoftware(b) as bs:
      bs.exec(...)


.. _board-uboot:

Board U-Boot
------------
If you are using U-Boot you'll probably want access to it from your testcases.
This is done using a U-Boot machine.  Like any software 'layer', a U-Boot
machine should use the :py:class:`tbot.machine.board.Connector` class.  The
shell should be a :py:class:`tbot.machine.board.UBootShell`.

In case your U-Boot is configured for autoboot, you'll want to use the optional
:py:class:`~tbot.machine.board.UBootAutobootIntercept` initializer as well.

**Example**:

.. code-block:: python

   class BoardUBoot(
       board.Connector,
       board.UBootShell,
   ):
       prompt = "U-Boot> "

.. autoclass:: tbot.machine.board.UBootShell
   :members:

.. autoclass:: tbot.machine.board.UBootAutobootIntercept
   :members:


.. _board-linux:

Board Linux
-----------
.. todo::

   Board Linux Docs
