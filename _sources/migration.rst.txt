Migrating from tbot 0.7.1
=========================
With version 0.8, the machines API was rewritten and its interface was changed
slightly in the process.  To migrate your configs and testcases, please read
through this page.

Testcases
---------
The days of the old cumbersome testcases are gone, with the new decorators,
things are **much** easier:

.. code-block:: python

   import tbot

   @tbot.testcase
   @tbot.with_lab
   def a_wild_testcase(lh):
      lh.exec0("uname", "-a")

   @tbot.testcase
   @tbot.with_uboot
   def check_uboot_version(ub):
      ub.exec0("version")

   @tbot.testcase
   @tbot.with_linux
   def board_linux_network(lnx):
      lnx.exec0("ip", "address")

The decorators are essentially syntactic sugar for checking whether a parameter
was given.  If it was not, they will call the appropriate ``tbot.acquire_*``
functions.  The first testcase example above would look like this without the decorator:

.. code-block:: python

   import tbot

   @tbot.testcase
   def a_wild_testcase(lh = None):
      if lh is None:
         lh = tbot.acquire_lab()

      with lh:
         lh.exec0("uname", "-a")

Machine Configuration
---------------------
Base Classes
~~~~~~~~~~~~
Machines now inherit from different classes than before.  Read through the
:mod:`tbot.machine` module docs for an overview of the new design.  The biggest
change is that instead of a single class, you now have to inherit from multiple
base classes at once.  The old classes map to the new ones like this:

+-----------------------------------------------+--------------------------------------------------------------+
| Old (single) base class                       | New (multiple) base classes                                  |
+===============================================+==============================================================+
| ``tbot.machine.linux.lab.LocalLabHost``       | | :class:`tbot.machine.connector.SubprocessConnector`        |
|                                               | | :class:`tbot.machine.linux.Bash` [#shell-type]_            |
| (Localhost as lab-host)                       | | :class:`tbot.machine.linux.Lab`                            |
+-----------------------------------------------+--------------------------------------------------------------+
| ``tbot.machine.linux.lab.SSHLabHost``         | | :class:`tbot.machine.connector.ParamikoConnector`          |
|                                               | | :class:`tbot.machine.linux.Bash` [#shell-type]_            |
| (Remote ssh-connected lab-host)               | | :class:`tbot.machine.linux.Lab`                            |
+-----------------------------------------------+--------------------------------------------------------------+
| ``tbot.machine.linux.SSHMachine``             | | :class:`tbot.machine.connector.SSHConnector`               |
|                                               | | :class:`tbot.machine.linux.Bash` [#shell-type]_            |
| (Remote ssh-connected machine)                | |                                                            |
+-----------------------------------------------+--------------------------------------------------------------+
| ``tbot.machine.linux.BuildMachine``           | | :class:`tbot.machine.linux.Builder`                        |
|                                               | | (Used as a mixin with other machine classes)               |
| Build-Host                                    |                                                              |
+-----------------------------------------------+--------------------------------------------------------------+
| ``tbot.machine.board.Board``                  | | :class:`tbot.machine.connector.ConsoleConnector`           |
|                                               | | :class:`tbot.machine.board.PowerControl` [#power]_         |
| (Hardware description of the board)           | | :class:`tbot.machine.board.Board`                          |
+-----------------------------------------------+--------------------------------------------------------------+
| ``tbot.machine.board.UBootMachine``           | | :class:`tbot.machine.board.Connector`                      |
|                                               | | :class:`tbot.machine.board.UBootAutobootIntercept` [#ab]_  |
| (U-Boot configuration)                        | | :class:`tbot.machine.board.UBootShell`                     |
+-----------------------------------------------+--------------------------------------------------------------+
| ``tbot.machine.board.LinuxWithUBootMachine``  | | :class:`tbot.machine.board.LinuxUbootConnector`            |
|                                               | | :class:`tbot.machine.board.LinuxBootLogin`                 |
| (Linux booted from U-Boot)                    | | :class:`tbot.machine.linux.Ash` [#shell-type]_             |
+-----------------------------------------------+--------------------------------------------------------------+
| ``tbot.machine.board.LinuxStandaloneMachine`` | | :class:`tbot.machine.board.Connector`                      |
|                                               | | :class:`tbot.machine.board.LinuxBootLogin`                 |
| (Linux booted directly after powerup)         | | :class:`tbot.machine.linux.Ash` [#shell-type]_             |
+-----------------------------------------------+--------------------------------------------------------------+

.. [#shell-type] This can of course be a different shell-class as well, depending on your setup.
.. [#power] This one is only needed if your hardware supports power switching.
.. [#ab] If U-Boot is configured to automatically boot, this class is needed.  Otherwise it is not and can be omitted.

Example
~~~~~~~
Here is a diff of a board config from old to new:

.. code-block:: diff

   -from tbot.machine import board, linux
   +from tbot.machine import connector, board, linux


   -class BeagleBoneBlack(board.Board):
   +class BeagleBoneBlack(connector.ConsoleConnector, board.PowerControl, board.Board):
        name = "bbb"

        def poweron(self):
   -        self.lh.exec0("magic-power-controller-tool", "on")
   +        self.host.exec0("magic-power-controller-tool", "on")

        def poweroff(self):
   -        self.lh.exec0("magic-power-controller-tool", "off")
   +        self.host.exec0("magic-power-controller-tool", "off")

   -    def console_check(self):
   -        if "off" not in self.lh.exec0("magic-power-controller-tool", "-l"):
   -            raise Exception("Board is already on!")
   +    def power_check(self):
   +        return "off" in self.lh.exec0("magic-power-controller-tool", "-l")

   -    def connect(self):
   -        return self.lh.new_channel("picocom", "-b", str(115200), "/dev/ttyUSB0")
   +    def connect(self, mach):
   +        return mach.open_channel("picocom", "-b", str(115200), "/dev/ttyUSB0")

   -class BBBUBoot(board.UBootMachine[BeagleBoneBlack]):
   +class BBBUBoot(board.Connector, board.UBootAutobootIntercept, board.UBootShell):
        name = "bbb-uboot"
        prompt = "=> "

   -class BBBLinux(board.LinuxWithUBootMachine[BeagleBoneBlack]):
   +class BBBLinux(board.LinuxUbootConnector, board.LinuxBootLogin, linux.Ash):
        name = "bbb-linux"
        uboot = BBBUBoot
        username = "root"
        password = None

        def do_boot(self, ub):
            ub.env("autoload", "no")
            ub.exec0("dhcp")

   -        return ["run", "netnfsboot"]
   +        return ub.boot("run", "netnfsboot")

    BOARD = BeagleBoneBlack
    UBOOT = BBBUBoot
    LINUX = BBBLinux


Machine Interaction
-------------------
There were a few minor changes to machine interaction as well.

* The ``stdout=...`` argument was removed.  Use :class:`tbot.machine.linux.RedirStdout`
  instead:

  .. code-block:: diff

      a_file = lh.fsroot / "tmp" / "somefile"

     -lh.exec0("echo", "bar", stdout=a_file)
     +lh.exec0("echo", "bar", linux.RedirStdout(a_file))

* ``linux.Env("varname")`` was removed.  You should query the variable using
  :meth:`LinuxShell.env() <tbot.machine.linux.LinuxShell.env>` instead:

  .. code-block:: diff

     -lh.exec0("cd", linux.Env("HOME"))
     +homedir = lh.env("HOME")
     +lh.exec0("cd", homedir)

* ``LabHost.new_channel()`` was removed.  Instead, clone the machine and call
  :meth:`~tbot.machine.linux.LinuxShell.open_channel` like this:

  .. code-block:: python

     with mach.clone() as cl:
         chan = cl.open_channel("telnet", "192.0.2.1")
