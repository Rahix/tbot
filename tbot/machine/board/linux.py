# TBot, Embedded Automation Tool
# Copyright (C) 2018  Harald Seiler
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import abc
import time
import typing
import tbot
from tbot.machine import board
from tbot.machine import linux
from tbot.machine import channel
from . import special

B = typing.TypeVar("B", bound=board.Board)
Self = typing.TypeVar("Self", bound="LinuxMachine")


class LinuxMachine(linux.LinuxMachine, board.BoardMachine[B]):
    """Abstract base class for board linux machines."""

    login_prompt = "login: "
    login_wait = 1.0

    @property
    @abc.abstractmethod
    def shell(self) -> typing.Type[linux.shell.Shell]:
        """Shell that is in use on the board."""
        pass

    @property
    def name(self) -> str:
        """Name of this linux machine."""
        return self.board.name + "-linux"

    @property
    def workdir(self: Self) -> "linux.Path[Self]":  # noqa: D102
        return linux.Path(self, "/tmp")

    @property
    @abc.abstractmethod
    def password(self) -> typing.Optional[str]:
        """Password for logging in once Linux has booted."""
        pass

    def __init__(self, b: typing.Union[B, board.UBootMachine[B]]) -> None:
        """Create a new instance of this LinuxMachine."""
        super().__init__(b.board if isinstance(b, board.UBootMachine) else b)

    def boot_to_shell(self, stream: typing.TextIO) -> str:
        """Wait for the login prompt."""
        chan = self._obtain_channel()
        output = ""

        output += chan.read_until_prompt(self.login_prompt, stream=stream)

        chan.send(self.username + "\n")
        stream.write(self.login_prompt + self.username + "\n")
        output += self.login_prompt + self.username + "\n"
        if self.password is not None:
            chan.read_until_prompt("word: ")
            chan.send(self.password + "\n")
            stream.write("Password: ****\n")
            output += "Password: ****\n"
        time.sleep(self.login_wait)
        chan.send("\n")
        chan.initialize(sh=self.shell)

        return output


class LinuxWithUBootMachine(LinuxMachine[B]):
    """
    Linux machine that boots from U-Boot.

    **Example Implementation**::

        from tbot.machine import board

        class MyBoard(board.Board):
            ...

        class MyBoardUBoot(board.UBootMachine[MyBoard]):
            ...

        class MyBoardLinux(board.LinuxWithUBootMachine[MyBoard]):
            uboot = MyBoardUBoot

            username = "root"
            password = None

            boot_commands = [
                ["tftp", board.Env("loadaddr"), "zImage"],
                ["bootz", board.Env("loadaddr")],
            ]

        BOARD = MyBoard
        UBOOT = MyBoardUBoot
        LINUX = MyBoardLinux

    .. py:attribute:: login_prompt: str = "login: "

        Prompt that indicates TBot should send the username.

    .. py:attribute:: username: str

        Username for logging in.

    .. py:attribute:: password: str

        Password for logging in. Can be :class:`None` to indicate that
        no password is needed.

    .. py:attribute:: login_wait: float = 1.0

        Time to wait after sending login credentials.

    .. py:attribute:: shell: tbot.machine.linux.shell.Shell = Ash

        Type of the shell that is the default on the board.

    .. py:attribute:: boot_commands: list[list[]]

        List of commands to boot Linux from U-Boot. Commands are a list,
        of the arguments that are given to :meth:`~tbot.machine.board.UBootMachine.exec0`

        By default, ``do_boot`` is called, but if ``boot_commands`` is defined, it will
        be used instead (and ``do_boot`` is ignored).

        **Example**::

            boot_commands = [
                ["setenv", "console", "ttyS0"],
                ["setenv", "baudrate", str(115200)],
                [
                    "setenv",
                    "bootargs",
                    board.Raw("console=${console},${baudrate}"),
                ],
                ["tftp", board.Env("loadaddr"), "zImage"],
                ["bootz", board.Env("loadaddr")],
            ]
    """

    boot_commands: typing.Optional[
        typing.List[typing.List[typing.Union[str, special.Special]]]
    ] = None

    def do_boot(
        self, ub: board.UBootMachine[B]
    ) -> typing.List[typing.Union[str, special.Special]]:
        """
        Run commands to boot linux on ``ub``.

        The last command, the one that actually kicks off the boot process,
        needs to be returned as a list of arguments.

        ``do_boot`` will only be called, if ``boot_commands`` is None.

        **Example**::

            def do_boot(
                self, ub: board.UBootMachine[B]
            ) -> typing.List[typing.Union[str, board.Special]]:
                ub.exec0("setenv", "console", "ttyS0")
                ub.exec0("setenv", "baudrate", str(115200))
                ub.exec0(
                    "setenv",
                    "bootargs",
                    board.Raw("console=${console},${baudrate}"),
                )
                ub.exec0("tftp", board.Env("loadaddr"), "zImage")

                return ["bootz", board.Env("loadaddr")]
        """
        return ["run", "bootcmd"]

    @property
    @abc.abstractmethod
    def uboot(self) -> typing.Type[board.UBootMachine[B]]:
        """U-Boot machine for this board."""
        pass

    def __init__(self, b: typing.Union[B, board.UBootMachine[B]]) -> None:  # noqa: D107
        super().__init__(b)
        if isinstance(b, board.UBootMachine):
            ub = b
            self.ub = None
        else:
            self.ub = self.uboot(b)
            ub = self.ub

        self.channel = ub.channel

        with tbot.log.EventIO(
            ["board", "linux", ub.board.name],
            tbot.log.c("LINUX").bold + f" ({self.name})",
            verbosity=tbot.log.Verbosity.QUIET,
        ) as boot_ev:
            if self.boot_commands is not None:
                for cmd in self.boot_commands[:-1]:
                    ub.exec0(*cmd)
                bootcmd = self.boot_commands[-1]
            else:
                bootcmd = self.do_boot(ub)

            # Make it look like a normal U-Boot command
            last_command = ub.build_command(*bootcmd)
            with tbot.log_event.command(ub.name, last_command) as ev:
                ev.prefix = "   <> "
                self.channel.send(last_command + "\n")
                log = self.boot_to_shell(channel.SkipStream(ev, len(last_command) + 1))

                boot_ev.data["output"] = log[len(last_command) + 1 :]

    def destroy(self) -> None:  # noqa: D102
        if self.ub is not None:
            self.ub.destroy()

    def _obtain_channel(self) -> channel.Channel:
        return self.channel


class LinuxStandaloneMachine(LinuxMachine[B]):
    """
    Linux machine that boots without U-Boot.

    **Example Implementation**::

        from tbot.machine import board
        from tbot.machine import linux

        class MyBoard(board.Board):
            ...

        class MyBoardLinux(board.LinuxStandaloneMachine[MyBoard]):
            username = "root"
            password = None
            shell = linux.shell.Bash


        BOARD = MyBoard
        LINUX = MyBoardLinux

    .. py:attribute:: login_prompt: str = "login: "

        Prompt that indicates TBot should send the username.

    .. py:attribute:: username: str

        Username for logging in.

    .. py:attribute:: password: str

        Password for logging in. Can be :class:`None` to indicate that
        no password is needed.

    .. py:attribute:: login_wait: float = 1.0

        Time to wait after sending login credentials.

    .. py:attribute:: shell: tbot.machine.linux.shell.Shell = Ash

        Type of the shell that is the default on the board.
    """

    def __init__(self, b: typing.Union[B, board.UBootMachine[B]]) -> None:  # noqa: D107
        super().__init__(b)
        if isinstance(b, board.UBootMachine):
            raise RuntimeError(f"{self!r} does not support booting from UBoot")

        if self.board.channel is not None:
            self.channel = self.board.channel
        else:
            raise RuntimeError("{board!r} does not support a serial connection!")

        with tbot.log.EventIO(
            ["board", "linux", self.board.name],
            tbot.log.c("LINUX").bold + f" ({self.name})",
            verbosity=tbot.log.Verbosity.QUIET,
        ) as ev:
            ev.prefix = "   <> "
            ev.verbosity = tbot.log.Verbosity.STDOUT
            log = self.boot_to_shell(ev)

            ev.data["output"] = log

    def destroy(self) -> None:  # noqa: D102
        self.channel.close()

    def _obtain_channel(self) -> channel.Channel:
        return self.channel
