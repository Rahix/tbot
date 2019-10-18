.. _configuration:

Configuration
=============
tbot has a configuration mechanism which allows selecting a board and lab from
the commandline using the ``-l`` and ``-b`` switches.  The configuration files
are just python scripts defining the classes for lab-host, board-hardware and
board-software.

.. _config-lab:

Lab Config
----------
The lab can be selected using ``-l lab-config.py`` on the command-line and the
selected lab will then be available to testcases by using the
:py:func:`tbot.acquire_lab` function.  The lab-config can be any python file
defining a lab-host machine.  To allow tbot to detect the machine, the python
module should have a global ``LAB`` which points to the machine's class.  For
best compatibility, the lab-host machine should inherit from
:py:class:`tbot.machine.linux.Lab`.

**Example**: ``lab-config.py``

.. code-block:: python

   from tbot.machine import connector, linux, board

   class MyLabHost(
       connector.ParamikoConnector,
       linux.Bash,
       linux.Lab,
   ):
       hostname = "my-lab.local"
       name = "my-lab"

       @property
       def workdir(self):
           return linux.Workdir.static(self, f"/work/{self.username}/tbot-workdir")

   # Tell tbot about the class by defining a global `LAB`
   LAB = MyLabHost

In this instance, tbot will connect to the lab via SSH and use
``/work/<user>/tbot-workdir`` for storing data during tests.  You could try out
your config using:

.. code-block:: shell-session

   $ tbot -l lab-config.py selftest_machine_labhost_shell

For further information about the configurable options, look at the docs for
the individual classes:

- :py:class:`tbot.machine.connector.ParamikoConnector`
- :py:class:`tbot.machine.linux.Bash` (which is just a
  :py:class:`tbot.machine.linux.LinuxShell`)
- :py:class:`tbot.machine.linux.Lab`

If you instead want to use your localhost as the lab-host, you should use a
:py:class:`tbot.machine.connector.SubprocessConnector` instead.


.. _config-board:

Board Config
------------
The board configuration is split into two parts:  The first part configures the
physical hardware and how to access it (called the *Board*) and the second part
defines the software running on it.

.. todo::

   At the moment, both the hardware and the software config live in the same
   file.  We plan to (optionally) separate this in the future to allow even
   more generic configurations.

Board-Hardware Config
~~~~~~~~~~~~~~~~~~~~~
The hardware is configured as a machine which turns on the board when accessed
and opens a serial-console.  It does not do any further interaction with the
board, to not make any assumptions about the software running on it.

Typically, the board config might look similar to this:

.. code-block:: python

   from tbot.machine import connector, board

   class MyBoard(
       connector.ConsoleConnector,
       board.PowerControl,
       board.Board,
   ):
       name = "myboard"

       def poweron(self):
           self.host.exec0("power-control.sh", "on")

       def poweroff(self):
           self.host.exec0("power-control.sh", "off")

       def connect(self, mach):
           # Open the serial console
           return mach.open_channel("picocom", "-b", "115200", "/dev/ttyUSB0")


   # Similarl to the `LAB`, the board needs to be made available as `BOARD`
   BOARD = MyBoard


This should be enough to allow accessing the board using the
``interactive_board`` testcase:

.. code-block:: shell-session

   $ tbot -l lab-config.py -b board-config.py -vv interactive_board

Next up, you need to configure the software running on your board.  If you have
U-Boot and want to access it from testcases, continue to the next section:
:ref:`config-board-uboot`.  If you do not have U-Boot or you don't need access
to U-Boot from your testcases, you can jump to
:ref:`config-board-linux-standalone`.

.. _config-board-uboot:

U-Boot Config
~~~~~~~~~~~~~
U-Boot is configured as another machine ontop of the 'hardware machine'.  It
looks like this:

.. code-block:: python

   from tbot.machine import board

   class MyBoardUBoot(
       board.Connector,
       board.UBootShell,
   ):
       prompt = "=> "

   # Make visible to tbot:
   UBOOT = MyBoardUBoot

If your U-Boot is configured with autoboot, you should also inherit the
:py:class:`~tbot.machine.board.UBootAutobootIntercept`:

.. code-block:: python

   from tbot.machine import board

   class MyBoardUBoot(
       board.Connector,
       board.UBootAutobootIntercept,
       board.UBootShell,
   ):
       prompt = "=> "

   # Make visible to tbot:
   UBOOT = MyBoardUBoot

If everything is configured correctly, you should now be able to access the
U-Boot shell using the ``interactive_uboot`` testcase:

.. code-block:: shell-session

   $ tbot -l lab-config.py -b board-config.py -vv interactive_uboot

In testcases, you can now access U-Boot by first acquiring the hardware using
:py:func:`tbot.acquire_board` and the acquiring U-Boot using
:py:func:`tbot.acquire_uboot`:

.. code-block:: python

   @tbot.testcase
   def footest():
       with tbot.acquire_board(lh) as b:
           with tbot.acquire_uboot(b) as ub:
               ub.exec0("version")

Linux (from U-Boot) Config
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. todo::

   This is a stub.  Look at the docs for :ref:`board-linux`,
   :py:class:`tbot.machine.board.LinuxUbootConnector`, and
   :py:class:`tbot.machine.board.LinuxBootLogin` for now ...


.. code-block:: python

   class BeagleBoneLinux(
       board.LinuxUbootConnector,
       board.LinuxBootLogin,
       linux.Bash,
   ):
       uboot = BeagleBoneUBoot
       username = "root"
       password = None

       def do_boot(self, ub: board.UBootShell) -> channel.Channel:
           ub.env("serverip", "192.168.1.1")
           ub.env("netmask", "255.255.0.0")
           ub.env("ipaddr", "192.168.1.2")
           ub.exec0("mw", "0x81000000", "0", "0x4000")
           ub.exec0("tftp", "0x81000000", "bbb/tbot/env.txt")
           ub.exec0("env", "import", "-t", "0x81000000")
           ub.env("rootpath", "/path/to/core-image-lsb-sdk-generic-armv7a-hf")

           return ub.boot("run", "netnfsboot")


   UBOOT = BeagleBoneUBoot
   LINUX = BeagleBoneLinux

.. _config-board-linux-standalone:

Linux (without U-Boot) Config
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. todo::

   This is a stub.  Look at the docs for :ref:`board-linux` and
   :py:class:`tbot.machine.board.LinuxBootLogin` for now ...

.. code-block:: python

   class BeagleBoneLinux(
       board.Connector,
       board.LinuxBootLogin,
       linux.Ash,
   ):
       username = "root"
       password = None


   LINUX = BeagleBoneLinux

.. _config-init:

Initializing a Machine
----------------------
After the basic setup sometimes you might need additional steps to bring the
machine into the state you need it in.  Example might be network setup in
U-Boot or disabling kernel console-logging in Linux.  You can do this by
defining a :meth:`tbot.machine.Machine.init` function:

.. code-block:: python

    class MyBoardLinux(..., linux.Ash):
        name = "myboard-lnx"

        ...

        def init(self):
            self.exec0("sysctl", "kernel.printk=1 4 1 4")
