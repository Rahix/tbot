# tbot, Embedded Automation Tool
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
import typing
import shlex
import shutil
import tbot
from tbot import machine
from tbot.machine import linux, channel
from . import special
from . import shell as sh

Self = typing.TypeVar("Self", bound="LinuxMachine")


class LinuxMachine(machine.Machine, machine.InteractiveMachine):
    """Generic machine that is running Linux."""

    @property
    def shell(self) -> typing.Type[sh.Shell]:
        """Shell that is in use on the board."""
        return sh.Bash

    @property
    @abc.abstractmethod
    def username(self) -> str:
        """Return the username for logging in on this machine."""
        pass

    @property
    @abc.abstractmethod
    def workdir(self: Self) -> "linux.Path[Self]":
        """Return a path where testcases can store data on this host."""
        pass

    @property
    def fsroot(self: Self) -> "linux.Path[Self]":
        """
        Return a path to the filesystem root.

        This is a helper to allow the following::

            vers = lh.fsroot / "proc" / "version"

        .. versionadded:: 0.6.6
        """
        return linux.Path(self, "/")

    @abc.abstractmethod
    def _obtain_channel(self) -> channel.Channel:
        pass

    def build_command(
        self: Self,
        *args: typing.Union[str, special.Special[Self], linux.Path[Self]],
        stdout: typing.Optional[linux.Path[Self]] = None,
    ) -> str:
        """
        Build the string representation of a command.

        :param args: Each arg is a token that will be sent to the shell. Can be
            either a str, a :class:`~linux.special.Special` or a Path that
            is associated with this host. Arguments will be escaped
            (a str like "a b" will not result in separate arguments to the
            command)
        :param Path stdout: File where stdout should be directed to
        :returns: A string that would be sent to the machine to execute the command
        :rtype: str
        """
        command = ""
        for arg in args:
            if isinstance(arg, linux.Path):
                if arg.host is not self:
                    raise machine.WrongHostException(self, arg)

                command += shlex.quote(arg._local_str()) + " "
            elif isinstance(arg, special.Special):
                command += arg.resolve_string(self) + " "
            elif isinstance(arg, str):
                command += shlex.quote(arg) + " "
            else:
                raise TypeError(f"{arg!r} is not a supported argument type!")

        if isinstance(stdout, linux.Path):
            if stdout.host is not self:
                raise Exception(
                    f"{self!r}: Provided {stdout!r} is not associated with this host"
                )
            stdout_file = stdout._local_str()
            command += f">{shlex.quote(stdout_file)} "

        return command[:-1]

    def exec(
        self: Self,
        *args: typing.Union[str, special.Special[Self], linux.Path[Self]],
        stdout: typing.Optional[linux.Path[Self]] = None,
        timeout: typing.Optional[float] = None,
    ) -> typing.Tuple[int, str]:
        """
        Run a command on this machine.

        :param args: Each arg is a token that will be sent to the shell. Can be
            either a str, a :class:`~linux.special.Special` or a Path that
            is associated with this host. Arguments will be escaped
            (a str like "a b" will not result in separate arguments to the
            command)
        :param Path stdout: File where stdout should be directed to
        :returns: Tuple with the exit code and a string containing the combined
            stdout and stderr of the command (with a trailing newline).
        :rtype: (int, str)
        """
        channel = self._obtain_channel()

        command = self.build_command(*args, stdout=stdout)

        with tbot.log_event.command(self.name, command) as ev:
            ret, out = channel.raw_command_with_retval(
                command, stream=ev, timeout=timeout
            )
            ev.data["stdout"] = out

        return ret, out

    def exec0(
        self: Self,
        *args: typing.Union[str, special.Special[Self], linux.Path[Self]],
        stdout: typing.Optional[linux.Path[Self]] = None,
        timeout: typing.Optional[float] = None,
    ) -> str:
        """
        Run a command on this machine and ensure it succeeds.

        :param args: Each arg is a token that will be sent to the shell. Can be
            either a str, a :class:`~linux.special.Special` or a Path that
            is associated with this host. Arguments will be escaped
            (a str like "a b" will not result in separate arguments to the
            command)
        :param Path stdout: File where stdout should be directed to
        :returns: A string containing the combined stdout and stderr of the
            command (with a trailing newline).
        :rtype: str
        """
        ret, out = self.exec(*args, stdout=stdout, timeout=timeout)

        if ret != 0:
            raise machine.CommandFailedException(self, self.build_command(*args), out)

        return out

    def test(
        self: Self,
        *args: typing.Union[str, special.Special[Self], linux.Path[Self]],
        stdout: typing.Optional[linux.Path[Self]] = None,
        timeout: typing.Optional[float] = None,
    ) -> bool:
        """
        Run a command and test if it succeeds.

        :param args: Each arg is a token that will be sent to the shell. Can be
            either a str, a :class:`~linux.special.Special` or a Path that
            is associated with this host. Arguments will be escaped
            (a str like "a b" will not result in separate arguments to the
            command)
        :param Path stdout: File where stdout should be directed to
        :returns: ``True`` if the return code is 0, else ``False``.
        :rtype: bool
        """
        ret, _ = self.exec(*args, stdout=stdout, timeout=timeout)
        return ret == 0

    def env(
        self: Self,
        var: str,
        value: typing.Union[str, special.Special[Self], linux.Path[Self], None] = None,
    ) -> str:
        """
        Get or set the value of an environment variable.

        :param str var: The variable's name
        :param str value: The value the var should be set to.  If this parameter
            is given, ``env`` will set, else it will just read a variable
        :rtype: str
        :returns: Value of the environment variable

        .. versionadded:: 0.6.2
        .. versionchanged:: 0.6.5
            You can use ``env()`` to set environment variables as well.
        """
        if value is not None:
            self.exec0("export", linux.F("{}={}", var, value))

        return self.exec0("printf", "%s", linux.Raw(f'"${{{var}}}"'))

    def interactive(self) -> None:
        """Drop into an interactive session on this machine."""
        channel = self._obtain_channel()

        # Generate the endstring instead of having it as a constant
        # so opening this files won't trigger an exit
        endstr = (
            "INTERACTIVE-END-"
            + hex(165_380_656_580_165_943_945_649_390_069_628_824_191)[2:]
        )

        size = shutil.get_terminal_size()
        cmd = self.shell.enable_editing()
        if cmd is not None:
            channel.raw_command(cmd)

        channel.raw_command(f"stty cols {size.columns}; stty rows {size.lines}")

        shell_cmd = self.build_command(*self.shell.command)
        channel.send(f"{shell_cmd}\n")
        cmd = self.shell.disable_history()
        if cmd is not None:
            channel.send(f"{cmd}\n")

        channel.send(self.shell.set_prompt(endstr) + "\n")
        channel.read_until_prompt(endstr)

        channel.send(f"{shell_cmd}\n")
        cmd = self.shell.set_prompt(
            f"\\[\\033[36m\\]{self.name}: \\[\\033[32m\\]\\w\\[\\033[0m\\]> "
        )
        channel.send(f"{cmd}\n")
        channel.read_until_prompt("> (\x1B\\[.*)?", regex=True)
        channel.send("\n")
        tbot.log.message("Entering interactive shell ...")

        channel.attach_interactive(end_magic=endstr)

        tbot.log.message("Exiting interactive shell ...")

        try:
            channel.raw_command("exit\n", timeout=0.5)
        except TimeoutError:
            raise RuntimeError("Failed to reacquire shell after interactive session!")

        cmd = self.shell.disable_editing()
        if cmd is not None:
            channel.raw_command(cmd)

    def subshell(
        self: Self,
        *args: typing.Union[str, special.Special[Self], linux.Path[Self]],
        shell: typing.Optional[typing.Type[sh.Shell]] = None,
    ) -> "_SubshellContext":
        """
        Start a subshell for isolating environment changes.

        If no arguments are supplied, the shell defined for this machine
        is used.  If arguments are given, they are expected to open
        a shell of type ``shell`` which defaults to the shell specified
        for this machine.

        **Example**::

            with tbot.acquire_lab() as lh:
                lh.exec0("echo", linux.Env("FOOVAR"))  # Empty result

                with lh.subshell():
                    lh.env("FOOVAR", "123")
                    lh.exec0("echo", linux.Env("FOOVAR"))  # 123

                lh.exec0("echo", linux.Env("FOOVAR"))  # Empty result

        :param Shell shell: Shell that is started

        .. versionadded:: 0.6.1
        """
        shell = shell or self.shell
        if args == ():
            args = tuple(shell.command)
        return _SubshellContext(self, shell, self.build_command(*args))


class _SubshellContext(typing.ContextManager):
    __slots__ = ("ch", "sh")

    def __init__(self, h: LinuxMachine, shell: typing.Type[sh.Shell], cmd: str) -> None:
        self.h = h
        self.ch = h._obtain_channel()
        self.sh = shell
        self.cmd = cmd

    def __enter__(self) -> None:
        tbot.log_event.command(self.h.name, self.cmd)
        self.ch.send(f"{self.cmd}\n")
        self.ch.initialize(sh=self.sh)

    def __exit__(self, exc_type, exc_value, traceback) -> None:  # type: ignore
        self.ch.send("exit\n")
        self.ch.read_until_prompt(channel.TBOT_PROMPT)
