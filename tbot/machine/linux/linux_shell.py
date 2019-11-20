# tbot, Embedded Automation Tool
# Copyright (C) 2019  Harald Seiler
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
import tbot
from .. import shell, channel
from . import path, workdir
from .special import Special

Self = typing.TypeVar("Self", bound="LinuxShell")


class LinuxShell(shell.Shell):
    """
    Base-class for linux shells.

    This class defines the common interface for linux shells.
    """

    @abc.abstractmethod
    def escape(
        self: Self, *args: typing.Union[str, Special[Self], path.Path[Self]]
    ) -> str:
        """
        Escape a string according to this shell's escaping rules.

        If multiple arguments are given, ``.escape()`` returns a string
        containing each argument as a separate shell token.  This means:

        .. code-block:: python

            bash.escape("foo", "bar")
            # foo bar

            bash.escape("foo bar", "baz")
            # "foo bar" baz

        :param \\*args: Arguments to be escaped.  See :ref:`linux-argtypes` for details.
        :returns: A string with quoted/escaped versions of the input arguments.
        """
        raise NotImplementedError("abstract method")

    def build_command(
        self: Self, *args: typing.Union[str, Special[Self], path.Path[Self]]
    ) -> str:
        tbot.log.warning(
            "The `build_command()` method is deprecated.  Please use `escape()` instead."
        )
        return self.escape(*args)

    @abc.abstractmethod
    def exec(
        self: Self, *args: typing.Union[str, Special[Self], path.Path[Self]]
    ) -> typing.Tuple[int, str]:
        """
        Run a command on this machine/shell.

        **Example**:

        .. code-block:: python

            retcode, output = mach.exec("uname", "-a")
            assert retcode == 0

        :param \\*args: The command as separate arguments per command-line
            token.  See :ref:`linux-argtypes` for more info.
        :rtype: tuple(int, str)
        :returns: A tuple with the return code of the command and its console
            output.  Note that the output is ``stdout`` and ``stderr`` merged.
            It will also contain a trailing newline in most cases.
        """
        raise NotImplementedError("abstract method")

    @abc.abstractmethod
    def exec0(
        self: Self, *args: typing.Union[str, Special[Self], path.Path[Self]]
    ) -> str:
        """
        Run a command and assert its return code to be 0.

        **Example**:

        .. code-block:: python

            output = mach.exec0("uname", "-a")

            # This will raise an exception!
            mach.exec0("false")

        :param \\*args: The command as separate arguments per command-line
            token.  See :ref:`linux-argtypes` for more info.
        :rtype: str
        :returns: The command's console output.  Note that the output is
            ``stdout`` and ``stderr`` merged.  It will also contain a trailing
            newline in most cases.
        """
        raise NotImplementedError("abstract method")

    @abc.abstractmethod
    def test(
        self: Self, *args: typing.Union[str, Special[Self], path.Path[Self]]
    ) -> bool:
        """
        Run a command and return a boolean value whether it succeeded.

        **Example**:

        .. code-block:: python

            if lnx.test("which", "dropbear"):
                tbot.log.message("Dropbear is installed!")

        :param \\*args: The command as separate arguments per command-line
            token.  See :ref:`linux-argtypes` for more info.
        :rtype: bool
        :returns: Boolean representation of commands success.  ``True`` if
            return code was ``0``, ``False`` otherwise.
        """
        raise NotImplementedError("abstract method")

    @abc.abstractmethod
    def env(
        self: Self, var: str, value: typing.Union[str, path.Path[Self], None] = None
    ) -> str:
        """
        Get or set an environment variable.

        **Example**:

        .. code-block:: python

            # Get the value of a var
            value = lnx.env("PATH")

            # Set the value of a var
            lnx.env("DEBIAN_FRONTEND", "noninteractive")

        :param str var: Environment variable name.
        :param tbot.machine.linux.Path,\\ str value: Optional value to set the
            variable to.
        :rtype: str
        :returns: Current (new) value of the environment variable.
        """
        raise NotImplementedError("abstract method")

    @abc.abstractmethod
    def open_channel(
        self: Self, *args: typing.Union[str, Special[Self], path.Path[Self]]
    ) -> channel.Channel:
        """
        Transform this machine into a channel for something else by running a command.

        This is meant to be used for tools like ``picocom`` which connect the
        terminal to a serial console.

        **Example**:

        .. code-block:: python

            ch = lnx.open_channel("picocom", "-b", "115200", "/dev/ttyUSB0")

            # You can now interact with the channel for the serial console directly

        :rtype: tbot.machine.channel.Channel
        """
        raise NotImplementedError("abstract method")

    @abc.abstractmethod
    def interactive(self) -> None:
        """
        Start an interactive session on this machine.

        This method will connect tbot's stdio to the machine's channel so you
        can interactively run commands.  This method is used by the
        ``interactive_lab`` and ``interactive_linux`` testcases.
        """
        raise NotImplementedError("abstract method")

    @abc.abstractmethod
    def subshell(self: Self) -> typing.ContextManager[Self]:
        """
        Start a subshell environment.

        Sometimes you need to isolate certain tests into their own shell
        environment.  This method returns a context manager which does this:

        .. code-block:: python

            lnx.env("FOO", "bar")

            with lnx.subshell():
                lnx.env("FOO", "baz")

            assert lnx.env("FOO") == "bar"
        """
        pass

    @property
    def username(self) -> str:
        """Current username."""
        return self.env("USER")

    @property
    def fsroot(self: Self) -> path.Path[Self]:
        """
        Path to the filesystem root of this machine, for convenience.

        .. code-block:: python

            p = lnx.fsroot / "usr" / "lib"
            assert p.is_dir()
        """
        return path.Path(self, "/")

    @property
    def workdir(self: Self) -> path.Path[Self]:
        """
        Path to a directory which testcases can use to store files in.

        If configured properly, tbot will make sure this directory exists.
        Testcases should be able to deal with corrupt or missing files in this
        directory.  Implementations should use :py:class:`tbot.machine.linux.Workdir`.

        **Example**:

        .. code-block:: python

            # This is the defaut implementation
            def workdir(self):
                return linux.Workdir(self, "/tmp/tbot-wd")
        """
        return workdir.Workdir.static(self, "/tmp/tbot-wd")
