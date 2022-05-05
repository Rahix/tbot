.. _configuration:

Configuration
=============
Configuration in tbot is used to allow reusing testcase code against multiple
target devices.  This works by putting a common interface between the two:
Testcases do not reference concrete machines but instead request access to
certain *roles*.  The configuration then supplies machine classes which fill
each of these roles.  The component sitting in the middle is tbot's
:ref:`context`.

tbot comes with a number of pre-defined roles in the :py:mod:`tbot.role`
module.  These serve as a generic baseline.  In complex environments, it often
makes sense to define custom roles as well.  This will be shown further down on
this page.

Simple Example
--------------
For a basic introduction, you can also check out the :ref:`quickstart` guide.
Here, the configuration that was created over there is shown again:

.. code-block:: python

   import tbot
   from tbot.machine import board, connector, linux

   class MyBoard(connector.ConsoleConnector, board.Board):
       baudrate = 115200
       serial_port = "/dev/ttyUSB0"

       def connect(self, mach):
           return mach.open_channel("picocom", "-b", str(self.baudrate), self.serial_port)

   def register_machines(ctx):
       ctx.register(MyBoard, tbot.role.Board)

This configuration module defines a machine class ``MyBoard``.  The magic is
then in the ``register_machines()`` function:  It will be called to activate
this configuration and its job is to register all machine classes for the
appropriate roles.  One machine class can be registered for multiple roles, but
the other way around is not possible:  Once a role is occupied, further
attempts to register a different machine for it will fail.

Default roles
-------------
As mentioned above, tbot comes with a number of pre-defined roles in the
:py:mod:`tbot.role` module.  Let's look at them in more detail.  Further down
on this page, examples for configuring these roles will also be shown.

- :py:class:`tbot.role.LabHost`:  This is the "central" host for hardware
  interaction.  Usually, this is where commands are executed to toggle board
  power and connect to a serial console.  By default (and in most simple
  setups), it is simply the localhost.  But it can also be a remote server to
  which an SSH connection needs to be established just as well.

  It makes sense to structure your tests around this role.  This will allow
  configurations to be more flexible in regards to the hardware lab.

- :py:class:`tbot.role.LocalHost`: While the :py:class:`~tbot.role.LabHost` is
  often the localhost as well, this role is guaranteed to reference the local
  machine.  Tests should use it when accessing local data, e.g. files or
  binaries which were distributed alongside the testcases.  A common pattern is
  to then first copy everything to the lab-host and from there to the target
  (or the other direction for downloads).

- :py:class:`tbot.role.BuildHost`: A role for a build-server.  When builds are
  not done locally, testcases can use this role to reference a build server.
  Even when this is the localhost in most cases, using the correct role in
  tests means that other configurations can easily move to remote builds when
  needed.

The above roles all describe some Linux machines in the environment.  The
following roles describe the actual "device under test" or embedded hardware.

It is important to understand that machines to not necessarily map to separate
physical hardware.  Especially for the embedded boards, it is common to have
multiple machines which access them in different ways.  Access is then often
exclusive between one or the other.

- :py:class:`tbot.role.Board`: This role describes the "physical" board and how
  to access it.  It does *not* make any assumptions about the software running
  on it.  Splitting into hardware and software this way allows reusing the
  software configuration across multiple physical boards of the same type in
  different environments.  This role should always use the
  :py:class:`board.Board <tbot.machine.board.Board>` shell-class.

- :py:class:`tbot.role.BoardUBoot`: This role describes a U-Boot running on the
  board.  It is, of course, only needed when your tests need to interact with
  U-Boot or custom bootloader commands are needed to boot the system.  This
  machine should "grab" the console from the :py:class:`tbot.role.Board`
  machine.  The common way to do this is using the :py:class:`board.Connector
  <tbot.machine.board.Connector>` connector.

- :py:class:`tbot.role.BoardLinux`: This role describes a Linux running on the
  board.  Similar to U-Boot, it should also grab the console from whatever
  machine is registered for :py:class:`tbot.role.Board`.  In most cases, this
  machine will need an initializer which waits for the login prompt and then
  logs in.  You can use :py:class:`board.LinuxBootLogin
  <tbot.machine.board.LinuxBootLogin>` for that.

  When a custom boot sequence is needed, this machine can also, for example,
  acquire the :py:class:`tbot.role.BoardUBoot` machine first, run some commands
  on it, and then take its console channel for itself.  This is what the
  :py:class:`board.LinuxUbootConnector <tbot.machine.board.LinuxUbootConnector>`
  does.

Configuring a lab-host
----------------------
Here are some examples of lab-host configuration.  The first example just uses
the localhost but adjusts tbot's working directory.  You could use this if the
default does not suit you.

.. code-block:: python

   import tbot
   from tbot.machine import connector, linux

   class LocalLab(connector.SubprocessConnector, linux.Bash):
       name = "local"

       @property
       def workdir(self):
           return linux.Workdir.xdg_data(self, "project-xyz")

   def register_machines(ctx):
       ctx.register(LocalLab, [tbot.role.LabHost, tbot.role.LocalHost])

As this machine is also the localhost, we register it for
:py:class:`tbot.role.LocalHost` as well.

The second example is a lab-host to which we need to connect with SSH:

.. code-block:: python

   import tbot
   from tbot.machine import connector, linux

   class RemoteLab(connector.SSHConnector, linux.Bash):
        hostname = "remote-lab.example.com"
        username = "lab-user"
        port = 2222

   def register_machines(ctx):
       ctx.register(RemoteLab, tbot.role.LabHost)

Check the :py:class:`connector.SSHConnector <tbot.machine.connector.SSHConnector>`
documentation for more details.

.. _config-board:

Configuring a board
-------------------
The :ref:`quickstart` guide already walks through this to some degree.  Here is
some more information.  The :py:class:`tbot.role.Board` role describes just the
physical hardware.  In most situations this means a serial console and
(ideally) a controllable power supply.

Serial Console
^^^^^^^^^^^^^^
The easiest way to access a serial console is to use the
:py:class:`connector.ConsoleConnector <tbot.machine.connector.ConsoleConnector>`.
It just needs a command to open a serial console - commonly I use `picocom`_.
`tio`_ might also be an interesting option.  Tools which do fancy screen
buffering like *minicom* or *screen* cannot be used here.

.. _picocom: https://github.com/npat-efault/picocom
.. _tio: https://github.com/tio/tio

.. code-block:: python

   import tbot
   from tbot.machine import connector, board

   class MyBoard(connector.ConsoleConnector, board.Board):
       def connect(self, mach):
           # mach is an open "channel" on the lab-host.  We can call the
           # console command on it using `open_channel()`.  The channel is then
           # returned.
           return mach.open_channel("picocom", "-b", "115200", "/dev/ttyUSB0")

   def register_machines(ctx):
       ctx.register(MyBoard, tbot.role.Board)

If the board is connected to your localhost, you can also use the
:py:class:`~tbot_contrib.connector.pyserial.PyserialConnector` from
:py:mod:`tbot_contrib`.

Finally, if your board does not have a serial console, please take a look at
:ref:`config-board-without-serial`.

Power Control
^^^^^^^^^^^^^
For real automation of the hardware, its power supply must be controllable or
there must be at least a way to trigger a hardware reset automatically.  In
either case, you can add this to the configuration using the
:py:class:`board.PowerControl <tbot.machine.board.PowerControl>` initializer:

.. code-block:: python

   import tbot
   from tbot.machine import connector, board

   class MyBoard(connector.ConsoleConnector, board.PowerControl, board.Board):
       def poweron(self):
           with tbot.ctx.request(tbot.role.LabHost) as lh:
               lh.exec0("sispmctl", "-o", "3")

       def poweroff(self):
           with tbot.ctx.request(tbot.role.LabHost) as lh:
               lh.exec0("sispmctl", "-f", "3")

       # Time to wait between poweroff and subsequent poweron.  Use this if
       # your board needs time until power is truly off.
       powercycle_delay = 0.5

       def connect(self, mach):
           return mach.open_channel("picocom", "-b", "115200", "/dev/ttyUSB0")

   def register_machines(ctx):
       ctx.register(MyBoard, tbot.role.Board)

If you cannot provide full control but just a way to trigger a reset, it could
look like this:

.. code-block:: python

   def poweron(self):
       with tbot.ctx.request(tbot.role.LabHost) as lh:
           lh.exec0("board-reset.sh")

   def poweroff(self):
       # Do nothing...
       pass

If nothing of that sort is possible, there are a few hacks that have proven to
work "well enough":

.. code-block:: python

   def poweron(self):
       """
       Integrate the human into the loop:  This will send a notification to the
       developer that they need to manually trigger a reset now:
       """
       with tbot.ctx.request(tbot.role.LocalHost) as lo:
           lo.exec0("notify-send", "Powercycle", "Powercycle foo board please!")
           tbot.log.message("Powercycle now!")

   def poweron(self):
       """
       This alternative tries to trigger a soft-reset by spamming various
       commands on the board console in hopes that one of them sticks.  It is
       not reliable at all but can be useful as an 80% kind of solution...
       """
       time.sleep(0.1)
       # try stopping any running program on the board's shell
       ch.sendcontrol("C")
       time.sleep(0.1)
       # try rebooting from Linux
       ch.sendline("reboot")
       # ... or if you also use U-Boot, try resetting from there.  the `cat` is
       # used to ensure we don't send the `reset` to Linux as that messes with
       # the terminal...
       ch.sendline("cat")
       ch.sendline("reset")

.. _config-board-linux:

Configuring Linux for a board
-----------------------------
Now that the "physical board" is configured, a second machine for the software
running on it is needed.  First, this section describes how to configure a
machine for a Linux system running on the board.

A "board software" machine is supposed to take the console channel from the
"physical board" machine.  To do this, there exists a special
:py:class:`board.Connector <tbot.machine.board.Connector>`.  It will first
instanciate the "physical board" machine, then take exclusive access to it and
acquire its console channel.

From there, in most cases an initializer is needed which waits for the login
prompt and then logs in.  tbot provides the :py:class:`board.LinuxBootLogin
<tbot.machine.board.LinuxBootLogin>` initializer for this.

Finally, the shell should be chosen according to the shell running on the
board.  tbot currently provides either :py:class:`linux.Bash
<tbot.machine.linux.Bash>` or :py:class:`linux.Ash <tbot.machine.linux.Ash>`.
When in doubt, choose ``Ash``.

Tying it all together, the configuration will look like this:

.. code-block:: python

   import tbot
   from tbot.machine import connector, board, linux

   class MyBoard(connector.ConsoleConnector, board.PowerControl, board.Board):
       # see above
       ...

   class MyBoardLinux(board.Connector, board.LinuxBootLogin, linux.Ash):
       # for board.LinuxBootLogin:
       username = "root"
       password = "hunter2"  # or `None` if no password is needed

   def register_machines(ctx):
       ctx.register(MyBoard, tbot.role.Board)
       ctx.register(MyBoardLinux, tbot.role.BoardLinux)

This should be enough to get a scriptable Linux session on the board.  If your
system has a particularly noisy kernel which keeps clobbering the login prompt,
give the :py:attr:`login_delay <tbot.machine.board.LinuxBootLogin.login_delay>`
setting a try.

It is often useful to run some commands directly after logging into Linux for
every testrun.  For example, to silence kernel log messages or to set some
environment variables:

.. code-block:: python

   class MyBoardLinux(board.Connector, board.LinuxBootLogin, linux.Ash):
       username = "root"
       password = None

       def init(self):
           # silence kernel log messages so they don't clobber the console
           self.exec0("sysctl", "kernel.printk=2 2 2 2")
           # set PAGER* environment variables to prevent any kind of pager from
           # running as pagers are not well scriptable.
           self.env("PAGER", "cat")
           self.env("SYSTEMD_PAGER", "cat")

That said, it is a good idea to keep this kind of initialization to a minimum.
In most cases, you will be better off performing such steps at the start of
each testcase which needs them instead.

.. _config-board-uboot:

Configuring U-Boot for a board
------------------------------
For lower level development, making U-Boot scriptable is often desirable.
Configuring a machine for U-Boot works much the same as with Linux. If your
board is configured to autoboot, you can use the
:py:class:`board.UBootAutobootIntercept <tbot.machine.board.UBootAutobootIntercept>`
initializer to stop it. For U-Boot interaction, there is a
:py:class:`board.UBootShell <tbot.machine.board.UBootShell>`.

.. code-block:: python

   import tbot
   from tbot.machine import connector, board

   class MyBoard(connector.ConsoleConnector, board.PowerControl, board.Board):
       # see above
       ...

   class MyBoardUBoot(board.Connector, board.UBootAutobootIntercept, board.UBootShell):
       # U-Boot prompt string
       prompt = "=> "

       # if needed, you can set a different autoboot prompt (regex):
       # autoboot_prompt = tbot.Re("Press DEL 4 times.{0,100}", re.DOTALL)
       # ... and the appropriate key-sequence:
       # autoboot_keys = "\x7f\x7f\x7f\x7f"

   def register_machines(ctx):
       ctx.register(MyBoard, tbot.role.Board)
       ctx.register(MyBoardUBoot, tbot.role.BoardUBoot)

Configuring a custom Linux boot sequence
----------------------------------------
Instead of waiting for Linux to boot automatically, you can use the U-Boot
configuration to boot into Linux using custom commands.  I use this a lot to
implement network boot on the fly.  It also means I can very easily customize
the boot-sequence without touching the target (for example with :ref:`cli-flags`).

From a working U-Boot configuration, the
:py:class:`board.LinuxUbootConnector <tbot.machine.board.LinuxUbootConnector>`
can be used to define a custom boot sequence:

.. code-block:: python

   import tbot
   from tbot.machine import connector, board, linux

   class MyBoard(connector.ConsoleConnector, board.PowerControl, board.Board):
       # see above
       ...

   class MyBoardUBoot(board.Connector, board.UBootAutobootIntercept, board.UBootShell):
       prompt = "=> "

   class MyBoardLinux(board.LinuxUbootConnector, board.LinuxBootLogin, linux.Ash):
       # for board.LinuxBootLogin:
       username = "root"
       password = "hunter2"

       # for board.LinuxUbootConnector:
       uboot = MyBoardUBoot
       def do_boot(self, ub):  # <- ub is the instance of MyBoardUBoot
           ub.env("autoload", "false")
           ub.exec0("dhcp")
           loadaddr = ub.ram_base + 0x02000000
           ub.exec0("tftp", hex(loadaddr), "1.2.3.4:my-board/fitImage")
           bootargs = ["root=/dev/nfs", "nfsroot=...", "ip=dhcp"]
           ub.env("bootargs", " ".join(bootargs))
           return ub.boot("bootm", hex(loadaddr))

   def register_machines(ctx):
       ctx.register(MyBoard, tbot.role.Board)
       ctx.register(MyBoardUBoot, tbot.role.BoardUBoot)
       ctx.register(MyBoardLinux, tbot.role.BoardLinux)

.. _config-board-without-serial:

Configuring a board without a serial console
--------------------------------------------
Maybe you have a board which does not have a hardware serial.  You can only
access it via SSH, for example.  tbot can still be used with such a setup.
In this case, the board machine should use the
:py:class:`connector.NullConnector <tbot.machine.connector.NullConnector>`.
It fills in the connector role but will raise an error if there are any
attempts to actually access the console.

From there, a Linux machine with a custom connection scheme is needed. It needs to:

1. Instantiate the board machine to power it on.  Ideally it should also get
   "hardware information" from it like the IP-address.
2. Wait for the device to show up.
3. Use the :py:class:`connector.SSHConnector
   <tbot.machine.connector.SSHConnector>` to connect to it.

As these steps need to happen before the connector, it is best to implement
them as a :py:class:`~tbot.machine.PreConnectInitializer`.

Here is a code sample for this:

.. code-block:: python

   import time
   import contextlib
   import tbot
   from tbot.machine import board, connector, linux

   class MyBoard(connector.NullConnector, board.PowerControl, board.Board):
       def poweron(self):
           with tbot.ctx.request(tbot.role.LabHost) as lh:
               lh.exec0("sispmctl", "-o", "4")

       def poweroff(self):
           with tbot.ctx.request(tbot.role.LabHost) as lh:
               lh.exec0("sispmctl", "-f", "4")

       ip_address = "192.168.1.100"

   class MyBoardWaitForSsh(tbot.machine.PreConnectInitializer):
       @contextlib.contextmanager
       def _init_pre_connect(self):
           with tbot.ctx() as cx:
               b = cx.request(tbot.role.Board)
               self.board = b
               lh = cx.request(tbot.role.LabHost)
               tbot.log.message("Waiting for SSH server...")
               while not lh.test("ssh", "-o", "BatchMode=yes", f"root@{self.board.ip_address}", "true"):
                   time.sleep(2)
               # now hand over to the SSHConnector
               yield None
               lh.exec("ps")

   class MyBoardLinux(MyBoardWaitForSsh, connector.SSHConnector, linux.Ash):
       @property
       def hostname(self):
           return self.board.ip_address

       username = "root"

   def register_machines(ctx):
       ctx.register(MyBoard, tbot.role.Board)
       ctx.register(MyBoardLinux, tbot.role.BoardLinux)
