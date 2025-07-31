.. _quickstart:

Quick Start
===========
This quick-start guide will introduce you step-by-step to setting up a tbot
environment for automating your development workflow.  Please start by
installing tbot as detailed in :ref:`installation`.

This guide assumes you have an embedded Linux system like a BeagleBone or
Raspberry Pi (or some other board) with a serial console you can access.

.. note::

   This version of the quick-start guide uses ``newbot``, tbot's new
   commandline tool.  It is easier to use than the old CLI tool (``tbot``).  At
   some point in the future, the old tool will be removed.  For migration,
   please first read this guide to familiarize yourself with the new tool.
   Then, you can find additional information in :ref:`cli` about switching to
   ``newbot``.

1. Directory Structure
----------------------
To start, let's set up a basic directory structure.  Importantly, you can do
this completely different - here is just a simple and proven suggestion.

.. code-block:: shell-session

   $ mkdir tbot-example && cd tbot-example && git init
   $ mkdir -p config/ tc/
   $ touch config/my_config.py tc/interactive.py tc/examples.py
   $ tree
   ./
   ├──config/
   │  └──my_config.py
   └──tc/
      ├──examples.py
      └──interactive.py

There are two directories here:

- ``config/``: This directory is a Python module containing all configurations.
  For now, there is only one.
- ``tc/``: This directory is a Python module containing "testcases".
  "Testcase" just means a callable routine which does something.  "Task" might
  also be an adequate description.

Next, we will fill ``tc/interactive.py`` with some "testcase" code.  This will
help with the next step.  Please add the following code to
``tc/interactive.py``.  I will explain what it does later in this guide.

.. code-block:: python

   import tbot

   @tbot.testcase
   def board() -> None:
       """Open an interactive session on the board's serial console."""
       with tbot.ctx.request(tbot.role.Board) as b:
           b.interactive()

   @tbot.testcase
   def linux() -> None:
       """Open an interactive session on the board's Linux shell."""
       with tbot.ctx.request(tbot.role.BoardLinux) as lnx:
           lnx.interactive()

If your board uses U-Boot and you also intend to interact with it, you can also
add this one:

.. code-block:: python

   @tbot.testcase
   def uboot() -> None:
       """Open an interactive session on the board's U-Boot shell."""
       tbot.ctx.teardown_if_alive(tbot.role.BoardLinux)
       with tbot.ctx.request(tbot.role.BoardUBoot) as ub:
           ub.interactive()

2. Simple Testcases
-------------------
Now it is time to write some testcases ourselves.  Again, testcase just means
"callable function"/"task" in tbot.  Start with the following skeleton in
``tc/examples.py``:

.. code-block:: python

   import tbot

   @tbot.testcase
   def hello_world():
       tbot.log.message("Hello World!")

You can now run this testcase like this:

.. html-console::

   <pre><font color="#f92672"><b>$</b></font> newbot tc.examples.hello_world
   <font color="#F4BF75"><b>tbot</b></font> starting ...
   <font color="#A5A5A1">├─</font>Calling <font color="#A1EFE4"><b>hello_world</b></font> ...
   <font color="#A5A5A1">│   ├─</font>Hello World!
   <font color="#A5A5A1">│   └─</font><font color="#A6E22E"><b>Done</b></font>. (0.000s)
   <font color="#A5A5A1">├─────────────────────────────────────────</font>
   <font color="#A5A5A1">└─</font><font color="#A6E22E"><b>SUCCESS</b></font> (0.218s)
   </pre>

As you can see, you need to pass a sort of module path to ``newbot`` to run a
testcase.  Under the hood, you can imagine tbot is doing nothing more than:

.. code-block:: python

   # newbot tc.examples.hello_world
   # ... essentially does:
   import tc.examples
   tc.examples.hello_world()

The next testcase will run some commands on the localhost (= the machine tbot
is running on).  To do this, we first need to introduce the concept of
machines:

3. Machines
-----------
Any "host" or board tbot can interact with is called a *machine*.  We can
interact with them by instantiating a machine and then calling methods on this
instance.  To make everything a bit more generic, instantiation usually happens
by *requesting* a **role**.  A role is later filled in with a concrete
*machine* in the configuration.  A few roles have default machines attached, so
for now, no config is needed. In practice:

.. code-block:: python

   import tbot

   @tbot.testcase
   def hello_machine():
       with tbot.ctx.request(tbot.role.LocalHost) as lo:
           lo.exec0("uname", "-a")
           host = lo.exec0("hostname")
           tbot.log.message(f"This host is called: {host}")

Add this ``hello_machine()`` testcase to ``tc/examples.py`` and run it:

.. html-console::

   <pre><font color="#f92672"><b>$</b></font> newbot tc.examples.hello_machine
   <font color="#F4BF75"><b>tbot</b></font> starting ...
   <font color="#A5A5A1">├─</font>Calling <font color="#A1EFE4"><b>hello_machine</b></font> ...
   <font color="#A5A5A1">│   ├─[</font><font color="#F4BF75">local</font>] uname -a
   <font color="#A5A5A1">│   │    </font>## Linux sandvich 5.17.4-arch1-1 #1 SMP PREEMPT Wed, 20 Apr 2022 18:29:28 +0000 x86_64 GNU/Linux
   <font color="#A5A5A1">│   ├─[</font><font color="#F4BF75">local</font>] hostname
   <font color="#A5A5A1">│   │    </font>## sandvich
   <font color="#A5A5A1">│   └─</font><font color="#A6E22E"><b>Done</b></font>. (0.070s)
   <font color="#A5A5A1">├─────────────────────────────────────────</font>
   <font color="#A5A5A1">└─</font><font color="#A6E22E"><b>SUCCESS</b></font> (0.210s)
   </pre>

In this case, the role :py:class:`tbot.role.LocalHost` is used.  It describes
the host tbot is running on.  After requesting an instance of it, we can use
methods on the instance to run commands.

:py:meth:`exec0() <tbot.machine.linux.LinuxShell.exec0>` runs a command and
asserts that its return code is 0.  It returns the command's output (both stdout
and stderr interleaved).  The command is passed as multiple arguments, each
containing one "shell token".  tbot automatically escapes everything correctly.
To make this more clear, here are a few shell commands and their equivalent
tbot call:

.. code-block:: python

   # uname -a
   lo.exec0("uname", "-a")
   # find / -name "*.git"
   lo.exec0("find", "/", "-name", "*.git")
   # echo '${this is not expanded}'
   lo.exec0("echo", "${this is not expanded}")
   # git commit -a -m "commit message"
   lo.exec0("git", "commit", "-a", "-m", "commit message")

Linux machines have a lot of other methods to make interaction easy.  Here is a
more involved example:

.. code-block:: python

   @tbot.testcase
   def machine_interaction():
       with tbot.ctx.request(tbot.role.LocalHost) as lo:
           # get the value of the ${HOME} environment variable
           home = lo.env("HOME")

           # test if it is a directory.  test() returns True if the command
           # succeeded and False otherwise
           if lo.test("test", "-d", home):
               tbot.log.message("${HOME} is a real directory!")

           # exec() returns a tuple of (retcode, output)
           retcode, output = lo.exec("systemctl", "status", "multi-user.target")
           if retcode != 0:
               tbot.log.warning("systemctl failed?")

For a full list, check the documentation for :ref:`linux-shells`.

There is one more method I want to highlight here: :py:meth:`interactive()
<tbot.machine.linux.LinuxShell.interactive>`.  It allows you to drop into an
interactive shell session at any time.  In its simplest form, we used it in
``tc/interactive.py`` at the very beginning.  But you can use it at any point
in your own code as well.  This is very useful while developing testcases.

4. Configuration
----------------
The configuration module tells tbot what machines exist beyond the localhost
and how to interact with each one.  Such machines might be a remote server
which can be reached over SSH, your board, or the Linux on your board.

The last two are important to distinguish:  The "bare" board is treated as a
separate machine from the Linux running on it.  This split tries to separate
the physical hardware from the "virtual" software running on it.  The software
might be the same for multiple boards, so this scheme allows reusing parts of
the configuration.

The configuration module in our case will be ``config.my_config`` and as such
it is stored in ``config/my_config.py``.  Let's start by creating a simple
configuration for a board with a serial console.  Please copy the following
code into ``config/my_config.py`` and adjust it appropriately:

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

``MyBoard`` is a class describing the "board machine".  In this case, it just
connects to the serial console using `picocom`_.  We will look at the details
of this class in the next section.

.. _picocom: https://github.com/npat-efault/picocom

The ``register_machines()`` function is special: It will be called by tbot to
"activate" this configuration.  Its job is to register all the new machines for
appropriate roles.  Here, we register ``MyBoard`` for the
:py:class:`tbot.role.Board` class.

We can already try out this configuration using one of the testcases from
earlier. Call the ``tc.interactive.board`` testcase and powercycle the board.
You will enter an session on the serial console where you can interact with the
board.  Press ``CTRL-D`` to exit.

.. html-console::

   <pre><font color="#f92672"><b>$</b></font> newbot -c config.my_config tc.interactive.board
   <font color="#F4BF75"><b>tbot</b></font> starting ...
   <font color="#A5A5A1">├─</font>Calling <font color="#A1EFE4"><b>board</b></font> ...
   <font color="#A5A5A1">│   ├─[</font><font color="#F4BF75">local</font>] picocom -q -b 115200 /dev/ttyUSB1
   <font color="#A5A5A1">│   ├─</font>Entering interactive shell (<b>CTRL+D to exit</b>) ...

   U-Boot 2022.01 (Apr 06 2022 - 14:09:55 +0000)

   CPU:   Freescale i.MX6UL rev1.1 528 MHz (running at 396 MHz)
   Reset cause: POR
   Scanning mmc 0:1...
   Found U-Boot script /boot/boot.scr
   1691 bytes read in 2 ms (825.2 KiB/s)
   ## Executing script at 86000000
   5490104 bytes read in 124 ms (42.2 MiB/s)
   Kernel image @ 0x82000000 [ 0x000000 - 0x53c5b8 ]
   ## Flattened Device Tree blob at 84000000
      Booting using the fdt blob at 0x84000000
      Loading Device Tree to 8ef71000, end 8ef7b0d2 ... OK

   Starting kernel ...

   [    2.658999] sd 0:0:0:0: [sda] No Caching mode page found
   [    2.664394] sd 0:0:0:0: [sda] Assuming drive cache: write through

   Xyz Linux 2022.04 test ttymxc5

   test login: root
   root@emb-imx6ul:~# uname -a
   Linux test 5.10.99 #1 Tue Feb 8 17:30:41 UTC 2022 armv7l GNU/Linux
   root@emb-imx6ul:~#
   <font color="#A5A5A1">│   └─</font><font color="#A6E22E"><b>Done</b></font>. (72.616s)
   <font color="#A5A5A1">├─────────────────────────────────────────</font>
   <font color="#A5A5A1">└─</font><font color="#A6E22E"><b>SUCCESS</b></font> (72.676s)
   </pre>

The ``-c`` argument is used to tell ``newbot`` which configuration to load.
Again, there is little magic here.  You can imagine tbot is just doing this:

.. code-block:: python

   # newbot -c config.my_config
   # ... essentially does:
   import config.my_config
   config.my_config.register_machines(tbot.ctx)

After that, the listed testcases are called like before.

A thing worth mentioning is that you can pass ``-c`` multiple times.  This
means you can modularize your configuration and mix-and-match from the
commandline.

5. Machines in depth
--------------------
Machines in tbot have two core parts:

- A "connector" which defines how to open the connection to this machine.  This
  can be opening a serial console
  (:py:class:`~tbot.machine.connector.ConsoleConnector`) or ssh-ing to a server
  (:py:class:`~tbot.machine.connector.SSHConnector`), for example.
- A "shell" which defines how to interact with the machine once the connection
  is established.  On Linux, this could be
  :py:class:`linux.Bash <tbot.machine.linux.Bash>` or
  :py:class:`linux.Ash <tbot.machine.linux.Ash>`.  Or for U-Boot, there is
  :py:class:`board.UBoot <tbot.machine.board.UBoot>`.  For the bare board above, we used
  :py:class:`board.Board <tbot.machine.board.Board>` as the shell.

A machine class must inherit from a connector class and a shell class.  These
classes usually demand that the machine class then defines additional
attributes and methods to configure them.  For example, the
:py:class:`~tbot.machine.connector.ConsoleConnector` requires you to define a
``connect()`` method.  Similarly, the
:py:class:`~tbot.machine.connector.SSHConnector` requires a ``hostname``
attribute.  You can check their documentation for more info.

In addition to connector and shell, there can be optional initializers.  These
come in many flavors: :py:class:`~tbot.machine.PreConnectInitializer`,
:py:class:`~tbot.machine.Initializer` (runs between connect and shell), and
:py:class:`~tbot.machine.PostShellInitializer`.

6. Power Control
----------------
One such initializer would be :py:class:`board.PowerControl
<tbot.machine.board.PowerControl>`.  It allows controlling board power
automatically.  If you have a switchable socket or relay connected to your
board's power, you can integrate it like this:

.. code-block:: python

   class MyBoard(connector.ConsoleConnector, board.PowerControl, board.Board):
       baudrate = 115200
       serial_port = "/dev/ttyUSB0"

       def poweron(self):
           with tbot.ctx.request(tbot.role.LocalHost) as lo:
               lo.exec0("sispmctl", "-o", "3")

       def poweroff(self):
           with tbot.ctx.request(tbot.role.LocalHost) as lo:
               lo.exec0("sispmctl", "-f", "3")

       def connect(self, mach):
           return mach.open_channel("picocom", "-b", str(self.baudrate), self.serial_port)

Now you don't need to manually powercycle the board anymore!

A quick tip:  If I can't control power for some hardware, I still use
:py:class:`board.PowerControl <tbot.machine.board.PowerControl>`.  Instead of
real commands, I instruct it to notify me of the need for a manual powercycle:

.. code-block:: python

       def poweron(self):
           with tbot.ctx.request(tbot.role.LocalHost) as lo:
               lo.exec0("notify-send", "Powercycle", "Powercycle foo board please!")
               tbot.log.message("Powercycle now!")

       def poweroff(self):
           pass

7. Board Linux
--------------
So far, tbot cannot really "interact" with the board.  We only got the
interactive console.  Let's change this by telling tbot about the Linux system
running on the board.  To do this, we need to define a new machine.  This
machine

1. "connects" to the existing board machine's console using the special
   :py:class:`board.Connector <tbot.machine.board.Connector>`,
2. then uses the :py:class:`board.LinuxBootLogin
   <tbot.machine.board.LinuxBootLogin>` initializer to wait for the login
   prompt and then log in,
3. and finally it will use a :py:class:`linux.Ash <tbot.machine.linux.Ash>`
   shell to interact with the Linux shell.

The configuration module in ``config/my_config.py`` now looks like this:

.. code-block:: python

   import tbot
   from tbot.machine import board, connector, linux

   class MyBoard(connector.ConsoleConnector, board.PowerControl, board.Board):
       baudrate = 115200
       serial_port = "/dev/ttyUSB0"

       def poweron(self):
           with tbot.ctx.request(tbot.role.LocalHost) as lo:
               lo.exec0("sispmctl", "-o", "3")

       def poweroff(self):
           with tbot.ctx.request(tbot.role.LocalHost) as lo:
               lo.exec0("sispmctl", "-f", "3")

       def connect(self, mach):
           return mach.open_channel("picocom", "-b", str(self.baudrate), self.serial_port)

   class MyBoardLinux(board.Connector, board.LinuxBootLogin, linux.Ash):
       username = "root"
       password = "hunter2"  # or `None` if no password is needed

   def register_machines(ctx):
       ctx.register(MyBoard, tbot.role.Board)
       ctx.register(MyBoardLinux, tbot.role.BoardLinux)

Similar to before, you can test this config with ``tc.interactive.linux`` to
get an interactive session on the board Linux.  But to really show where tbot
provides added value, let's write a testcase to automate something.  Add this
to ``tc/examples.py``:

.. code-block:: python

   import tbot

   @tbot.testcase
   def board_linux():
       with tbot.ctx.request(tbot.role.BoardLinux) as lnx:
           lnx.exec0("ip", "address")
           lnx.exec0("uname", "-a")
           lnx.exec0("cat", "/etc/os-release")

Run it!

.. html-console::

   <pre><font color="#f92672"><b>$</b></font> newbot -c config.my_config tc.examples.board_linux
   <font color="#F4BF75"><b>tbot</b></font> starting ...
   <font color="#A5A5A1">├─</font>Calling <font color="#A1EFE4"><b>board_linux</b></font> ...
   <font color="#A5A5A1">│   ├─</font>[<font color="#F4BF75">local</font>] <font color="#A5A5A1">picocom -q -b 115200 /dev/ttyUSB0</font>
   <font color="#A5A5A1">│   ├─</font><b>POWERON</b> (my-board)
   <font color="#A5A5A1">│   ├─</font>[<font color="#F4BF75">local</font>] <font color="#A5A5A1">sispmctl -o 3</font>
   <font color="#A5A5A1">│   │    </font>## Accessing Gembird #0 USB device 002
   <font color="#A5A5A1">│   │    </font>## Switched outlet 3 on
   <font color="#A5A5A1">│   ├─</font><b>LINUX</b> (my-board-linux)
   <font color="#A5A5A1">│   │    </font>&lt;&gt;
   <font color="#A5A5A1">│   │    </font>&lt;&gt; U-Boot 2022.01 (Apr 06 2022 - 14:09:55 +0000)
   <font color="#A5A5A1">│   │    </font>&lt;&gt;
   <font color="#A5A5A1">│   │    </font>&lt;&gt; CPU:   Freescale i.MX6UL rev1.1 528 MHz (running at 396 MHz)
   <font color="#A5A5A1">│   │    </font>&lt;&gt; Reset cause: POR
   <font color="#A5A5A1">│   │    </font>&lt;&gt; Scanning mmc 0:1...
   <font color="#A5A5A1">│   │    </font>&lt;&gt; Found U-Boot script /boot/boot.scr
   <font color="#A5A5A1">│   │    </font>&lt;&gt; 1691 bytes read in 2 ms (825.2 KiB/s)
   <font color="#A5A5A1">│   │    </font>&lt;&gt; ## Executing script at 86000000
   <font color="#A5A5A1">│   │    </font>&lt;&gt; 5490104 bytes read in 124 ms (42.2 MiB/s)
   <font color="#A5A5A1">│   │    </font>&lt;&gt; Kernel image @ 0x82000000 [ 0x000000 - 0x53c5b8 ]
   <font color="#A5A5A1">│   │    </font>&lt;&gt; ## Flattened Device Tree blob at 84000000
   <font color="#A5A5A1">│   │    </font>&lt;&gt;    Booting using the fdt blob at 0x84000000
   <font color="#A5A5A1">│   │    </font>&lt;&gt;    Loading Device Tree to 8ef71000, end 8ef7b0d2 ... OK
   <font color="#A5A5A1">│   │    </font>&lt;&gt;
   <font color="#A5A5A1">│   │    </font>&lt;&gt; Starting kernel ...
   <font color="#A5A5A1">│   │    </font>&lt;&gt;
   <font color="#A5A5A1">│   │    </font>&lt;&gt; [    2.658999] sd 0:0:0:0: [sda] No Caching mode page found
   <font color="#A5A5A1">│   │    </font>&lt;&gt; [    2.664394] sd 0:0:0:0: [sda] Assuming drive cache: write through
   <font color="#A5A5A1">│   │    </font>&lt;&gt;
   <font color="#A5A5A1">│   │    </font>&lt;&gt; Xyz Linux 2022.04 test ttymxc5
   <font color="#A5A5A1">│   │    </font>&lt;&gt;
   <font color="#A5A5A1">│   │    </font>&lt;&gt; test login:
   <font color="#A5A5A1">│   ├─</font>[<font color="#F4BF75">my-board-linux</font>] <font color="#A5A5A1">ip address</font>
   <font color="#A5A5A1">│   │    </font>## 1: lo: &lt;LOOPBACK,UP,LOWER_UP&gt; mtu 65536 qdisc noqueue qlen 1000
   <font color="#A5A5A1">│   │    </font>##     inet 127.0.0.1/8 scope host lo
   <font color="#A5A5A1">│   │    </font>##        valid_lft forever preferred_lft forever
   <font color="#A5A5A1">│   │    </font>## 2: eth0: &lt;BROADCAST,MULTICAST,UP,LOWER_UP&gt; mtu 1500 qdisc pfifo_fast qlen 1000
   <font color="#A5A5A1">│   │    </font>##     inet 10.0.0.100/16 brd 10.10.255.255 scope global dynamic eth0
   <font color="#A5A5A1">│   │    </font>##        valid_lft 85290sec preferred_lft 85290sec
   <font color="#A5A5A1">│   ├─</font>[<font color="#F4BF75">my-board-linux</font>] <font color="#A5A5A1">uname -a</font>
   <font color="#A5A5A1">│   │    </font>## Linux test 5.10.99 #1 Tue Feb 8 17:30:41 UTC 2022 armv7l GNU/Linux
   <font color="#A5A5A1">│   ├─</font>[<font color="#F4BF75">my-board-linux</font>] <font color="#A5A5A1">cat /etc/os-release</font>
   <font color="#A5A5A1">│   │    </font>## ID=test
   <font color="#A5A5A1">│   │    </font>## NAME=&quot;Xyz Linux&quot;
   <font color="#A5A5A1">│   │    </font>## VERSION=&quot;2022.04&quot;
   <font color="#A5A5A1">│   │    </font>## VERSION_ID=2022.04
   <font color="#A5A5A1">│   │    </font>## PRETTY_NAME=&quot;Xyz Linux 2022.04&quot;
   <font color="#A5A5A1">│   ├─</font><b>POWEROFF</b> (my-board)
   <font color="#A5A5A1">│   ├─</font>[<font color="#F4BF75">local</font>] <font color="#A5A5A1">sispmctl -f 4</font>
   <font color="#A5A5A1">│   │    </font>## Accessing Gembird #0 USB device 002
   <font color="#A5A5A1">│   │    </font>## Switched outlet 4 off
   <font color="#A5A5A1">│   └─</font><font color="#A6E22E"><b>Done</b></font>. (32.864s)
   <font color="#A5A5A1">├─────────────────────────────────────────</font>
   <font color="#A5A5A1">└─</font><font color="#A6E22E"><b>SUCCESS</b></font> (32.925s)
   </pre>

That's it for a basic overview of tbot!  Here are links to resources you could
dive into next:

- :ref:`cli`: The ``newbot`` commandline interface
- :ref:`configuration`: More details on configuration
- :ref:`context`: The mechanism for requesting machine instances
