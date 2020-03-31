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

   .. autoattribute:: tbot.machine.board.UBootShell.boot_timeout

      Maximum time from power-on to U-Boot shell.

      If tbot can't reach the U-Boot shell during this time, an exception will be thrown.

.. autoclass:: tbot.machine.board.UBootAutobootIntercept
   :members:


.. _board-linux:

Board Linux
-----------
The board's Linux machine can be configured in different ways, depending on
your setup and needs.

- If you do not need any bootloader interaction, you can define it in a way
  that goes straight from power-on to waiting for Linux.  This is done very
  similarly to the U-Boot machine above, by using the
  :py:class:`board.Connector <tbot.machine.board.Connector>`.
- If you do need bootloader interaction (because of manual commands to boot
  Linux for example), you should instead use the much more powerful
  :py:class:`board.LinuxUbootConnector <tbot.machine.board.LinuxUbootConnector>`.
  This class allows to boot Linux from U-Boot, either by passing it an existing
  U-Boot machine, or by automatically waiting for U-Boot first and then booting
  Linux.

In code, the two options look like this:

**Example for a standalone Linux (no bootloader interaction)**:

.. code-block:: python

   from tbot.machine import board, linux

   class StandaloneLinux(
       board.Connector,
       board.LinuxBootLogin,
       linux.Bash,
   ):
       # No config for the connector needed

       # LinuxBootLogin handles waiting for Linux to boot & logging in
       username = "root"
       password = "hunter2"

**Example for a Linux booting from U-Boot**:

.. code-block:: python

   from tbot.machine import board, linux

   class MyUBoot(board.Connector, board.UBootShell):
       ...

   class LinuxFromUBoot(
       board.LinuxUbootConnector,
       board.LinuxBootLogin,
       linux.Bash,
   ):
       # Configuration for LinuxUbootConnector
       uboot = MyUBoot  # <- Our UBoot machine

       def do_boot(self, ub):  # <- Procedure to boot Linux
          ub.env("autoload", "false")
          ub.exec0("dhcp")
          return ub.boot("run", "nfsboot")

       # LinuxBootLogin handles waiting for Linux to boot & logging in
       username = "root"
       password = "hunter2"

With both options, you'll use the
:py:class:`~tbot.machine.board.LinuxBootLogin` initializer to handle the boot
and login.

.. autoclass:: tbot.machine.board.LinuxUbootConnector
   :members:

.. autoclass:: tbot.machine.board.LinuxBootLogin
   :members:
