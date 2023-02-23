tbot Documentation
==================
Welcome to *tbot*!  *tbot* automates the development workflow for embedded
systems software.  This automation can then also be used for running tests
against real hardware, even in CI.

At its core, tbot is a library for interacting with remote hosts over various
connections.  For example, a target board can be accessed via serial console.
Or a TFTP-server via SSH.  tbot allows managing all these connections in
"parallel".  This means, you can orchestrate complex sequences of interaction
between them.

At the moment, the main focus of tbot lies in embedded Linux systems.  Support
for other systems is definitely intended to be added, too.

To show what tbot can help you with, here are a few simple example usecases:

**Boot into Linux and run a few commands over serial console**:

.. code-block:: python

   @tbot.testcase
   def test_linux_simple():
       # request serial connection to Linux on the board
       with tbot.ctx.request(tbot.role.BoardLinux) as lnx:
           # now we can run commands
           lnx.exec0("uname", "-a")

           # or, for example, read a file from the target
           cmdline = (lnx.fsroot / "proc" / "cmdline").read_text()

**Define custom commands to boot Linux**:

.. code-block:: python

   class CustomBoardLinux(board.LinuxUbootConnector, board.LinuxBootLogin, linux.Bash):
       username = "root"
       password = None

       def do_boot(self, uboot):
           # set `autoload` env-var to false to prevent automatic DHCP-boot
           uboot.env("autoload", "false")

           # get an IP-address
           uboot.exec0("dhcp")

           # download kernel + initramfs from TFTP server
           loadaddr = 0x82000000
           uboot.exec0("tftp", hex(loadaddr), f"{tftp_ip}:{kernel_image_path}")

           # and boot it!
           return uboot.boot("bootm", hex(loadaddr))

**Network speed test between a board and server**:

.. code-block:: python

   @tbot.testcase
   def test_ethernet_speed():
       with tbot.ctx() as cx:
           # boot into Linux on the board and acquire a shell-session
           lnx = cx.request(tbot.role.BoardLinux)

           # use ssh to connect to a network server to test against
           lh = cx.request(tbot.role.LabHost)

           # start iperf server
           with lh.run("iperf", "-s") as iperf_server:
               # and display its output while waiting for startup
               iperf_server.read_until_timeout(2)

               # now run iperf client on DUT
               tx_report = lnx.exec0("iperf", "-c", server_ip)

               # exit the server with CTRL-C
               tbot.log.message("Server Output:")
               iperf_server.sendcontrol("C")
               iperf_server.terminate0()


.. toctree::
   :maxdepth: 2
   :caption: Guides

   installation
   quickstart
   cli
   configuration
   recipes
   logging
   context
   pytest
   migration

.. toctree::
   :maxdepth: 1
   :caption: Core Modules

   modules/main
   modules/log
   modules/machine
   modules/machine_linux
   modules/machine_board
   modules/machine_connector
   modules/machine_shell
   modules/machine_channel
   modules/error
   modules/role
   modules/selectable

.. toctree::
   :maxdepth: 1
   :caption: Testcase Modules

   modules/tc
   contrib/connector
   contrib/gdb
   contrib/linux
   contrib/locking
   contrib/swupdate
   contrib/timing
   contrib/uboot
   contrib/utils

.. toctree::
   :maxdepth: 1
   :caption: Info

   CHANGELOG
   CONTRIBUTING
   LICENSE

Indices and tables
==================
- :ref:`genindex`
- :ref:`modindex`
- :ref:`search`
