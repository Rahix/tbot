Configuration
=============
tbot's configuration is also done in python.  There are two parts that can
be configured: The lab and the board.  If no lab is configured, tbot creates
a :class:`~tbot.machine.linux.lab.LocalLabHost`.  If no board is configured,
testcases trying to access it simply fail.

Lab Config
----------
The lab config can be chosen with the ``-l`` commandline parameter.  It should
be a python module with a global ``LAB`` that is a class derived from
:class:`~tbot.machine.linux.LabHost`.  It might look like this::

    import getpass
    import tbot
    from tbot.machine.linux import lab
    from tbot.machine import linux


    class PolluxLab(lab.SSHLabHost):
        name = "pollux"
        hostname = "pollux.denx.de"
        username = getpass.getuser()

        @property
        def workdir(self) -> "linux.Path[PolluxLab]":
            return linux.Workdir.static(self, f"/work/{self.username}/tbot-workdir")


    LAB = PolluxLab

For the list of possible parameters, take a look at the :class:`~tbot.machine.linux.lab.LocalLabHost`
and :class:`~tbot.machine.linux.lab.SSHLabHost` classes.

Board Config
------------
The board config can be chosen with the ``-b`` commandline parameter.  It should
be a python module with at least a global ``BOARD`` that is a class derived from
:class:`~tbot.machine.board.Board`.  If applicable, it can also export the
``UBOOT`` global which should be a class derived from :class:`~tbot.machine.board.UBootMachine`
and ``LINUX`` which should be derived from :class:`~tbot.machine.board.LinuxMachine`.
If both ``UBOOT`` and ``LINUX`` are exported, ``LINUX`` should be
a :class:`~tbot.machine.board.LinuxWithUBootMachine`.  But this is not enforced.

An example board config might look like this::

    from tbot.machine import board
    from tbot.machine import linux


    class BeagleBoneBlack(board.Board):
        name = "bbb"
        connect_wait = 3.0

        def poweron(self) -> None:
            self.lh.exec0("remote_power", self.name, "on")

        def poweroff(self) -> None:
            self.lh.exec0("remote_power", self.name, "off")

        def connect(self) -> channel.Channel:
            return self.lh.new_channel("connect", self.name)


    class BeagleBoneUBoot(board.UBootMachine[BeagleBoneBlack]):
        prompt = "=> "


    class BeagleBoneLinux(board.LinuxWithUBootMachine[BeagleBoneBlack]):
        uboot = BeagleBoneUBoot
        username = "root"
        password = None
        shell = linux.shell.Bash  # Setting the right shell is very important!
        boot_commands = [
            ["setenv", "serverip", "192.168.1.1"],
            ["setenv", "netmask", "255.255.0.0"],
            ["setenv", "ipaddr", "192.168.20.95"],
            ["mw", "0x81000000", "0", "0x4000"],
            ["tftp", "0x81000000", "bbb/tbot/env.txt"],
            ["env", "import", "-t", "0x81000000"],
            ["setenv", "rootpath", "/opt/..."],
            ["run", "netnfsboot"],
        ]


    BOARD = BeagleBoneBlack
    UBOOT = BeagleBoneUBoot
    LINUX = BeagleBoneLinux


For info on the possible configuration options, checkout the docs for
:class:`~tbot.machine.board.Board`,
:class:`~tbot.machine.board.UBootMachine`,
:class:`~tbot.machine.board.LinuxWithUBootMachine`, and
:class:`~tbot.machine.board.LinuxStandaloneMachine`.
