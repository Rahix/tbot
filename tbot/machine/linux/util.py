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

import typing
from typing import Any

import tbot.error
from tbot import machine
from tbot.machine import channel, linux

M = typing.TypeVar("M", bound="linux.LinuxShell")


def wait_for_shell(ch: channel.Channel) -> None:
    # Repeatedly sends `echo TBOT''LOGIN\r`.  At some point, the shell
    # interprets this command and prints out `TBOTLOGIN` because of the
    # quotation-marks being removed.  Once we detect this, this function
    # can return, knowing the shell is now running on the other end.
    #
    # Credit to Pavel for this idea!
    timeout = 0.2
    while True:
        ch.sendline("echo TBOT\\LOGIN")
        try:
            ch.expect("TBOTLOGIN", timeout=timeout)
            break
        except TimeoutError:
            # Increase the timeout after the first try because the remote might
            # just be a bit slow to get ready.  If we spam it too much, we will
            # actually slow down the shell initialization...
            timeout = 3.0


def posix_fetch_return_code(ch: channel.Channel, mach: M) -> int:
    ch.sendline("echo $?", read_back=True)
    retcode_str = ch.read_until_prompt()
    try:
        return int(retcode_str)
    except ValueError:
        raise tbot.error.InvalidRetcodeError(mach, retcode_str) from None


def posix_environment(
    mach: M, var: str, value: "typing.Union[str, linux.Path[M], None]" = None
) -> str:
    if value is not None:
        mach.exec0("export", linux.Raw(f"{mach.escape(var)}={mach.escape(value)}"))
        if isinstance(value, linux.Path):
            return value.at_host(mach)
        else:
            return value
    else:
        # Escape environment variable name, unless it is one of a few special names
        if var not in ["!", "$"]:
            var = mach.escape(var)
        # Add a space in front of the expanded environment variable to ensure
        # values like `-E` will not get picked up as parameters by echo.  This
        # space is then cut away again so calling tests don't notice this trick.
        return mach.exec0("echo", linux.Raw(f'" ${{{var}}}"'))[1:-1]


def shell_sanity_check(mach: M) -> None:
    mach.ch.sendline("echo TBOT-SANITY-CHECK", read_back=True)
    output = mach.ch.read_until_prompt()
    if output != "TBOT-SANITY-CHECK\n":
        raise tbot.error.UncleanShellError(mach)


# Type alias for the command context function/generator.  This function needs
# to be provided by the shell and contains the actual implementation of
# spawning an interactive command (and cleaning up / checking the return code
# once it is done).
#
# It works as follows:  The LinuxShell.run() implementation defines
# a cmd_context function with the following structure:
#
#   def cmd_context(
#       proxy_ch: util.RunCommandProxy,
#   ) -> typing.Generator[str, None, typing.Tuple[int, str]]:
#       # Spawn the command (on `proxy_ch`) and setup the channel for interaction.
#       proxy_ch.sendline(cmd + "\n", read_back=True)
#
#       # Yield the command string
#       yield cmd
#
#       # Wait for command to complete and return retcode and final output
#       output = proxy_ch.read_until_prompt()
#       proxy_ch.sendline("echo $?\n", read_back=True)
#       retcode = int(proxy_ch.read_until_prompt())
#
#       return (retcode, output)
#
# Then, the .run() implementation uses RunCommandProxy._ctx() to create the actual context:
#
#   yield from RunCommandProxy._ctx(self.ch, cmd_context)
CMD_CONTEXT = typing.Callable[
    ["RunCommandProxy"], typing.Generator[str, None, typing.Tuple[int, str]]
]


class RunCommandProxy(channel.Channel):
    """
    Proxy for interacting with a running command.

    A ``RunCommandProxy`` is created with a context-manager and
    :py:meth:`LinuxShell.run() <tbot.machine.linux.LinuxShell.run>`.

    **Example**:

    .. code-block:: python

        with lh.run("gdb", lh.workdir / "a.out") as gdb:
            gdb.sendline("target remote 127.0.0.1:3333")
            gdb.sendline("load")
            gdb.sendline("mon reset halt")

            gdb.sendline("quit")
            gbd.terminate0()

    A ``RunCommandProxy`` has all methods of a :py:class:`~tbot.machine.channel.Channel`
    for interacting with the remote.  Additionally, a few more methods exist
    which are necessary to end a command's invokation properly.  **You must
    always call one of them before leaving the context-manager!**  These methods are:
    """

    _write_blacklist: typing.List[int]
    _c: channel.ChannelIO
    _c2: channel.ChannelIO

    @staticmethod
    def _ctx(
        *,
        channel: channel.Channel,
        context: CMD_CONTEXT,
        host: "machine.Machine",
        args: Any,
    ) -> "typing.Iterator[RunCommandProxy]":
        """
        Helper function for LinuxShell.run() implementations.  See the comment
        near the CMD_CONTEXT definition in this file for more details.
        """
        with channel.borrow() as ch:
            proxy = RunCommandProxy(ch, context, host, args)

            try:
                yield proxy
            except Exception as e:
                proxy._cmd_context.throw(e.__class__, e)
            proxy._assert_end()

    def __new__(
        cls,
        chan: channel.Channel,
        cmd_context: CMD_CONTEXT,
        host: "machine.Machine",
        args: Any,
    ) -> "RunCommandProxy":
        chan.__class__ = cls
        return typing.cast(RunCommandProxy, chan)

    def __init__(
        self,
        chan: channel.Channel,
        cmd_context: CMD_CONTEXT,
        host: "machine.Machine",
        args: Any,
    ) -> None:
        self._proxy_alive = True
        self._cmd_context = cmd_context(self)
        self._cmd = next(self._cmd_context)
        self._c2 = self._c
        self._exc_host = host
        self._exc_args = args

    def terminate0(self) -> str:
        """
        Wait for the command to end **successfully**.

        Asserts that the command returned with retcode 0.  If it did not, an
        exception is raised.

        :returns: Remaining output of the command until completion.
        :rtype: str
        """
        retcode, output = self.terminate()
        if retcode != 0:
            raise tbot.error.CommandFailure(
                self._exc_host, self._exc_args, repr=self._cmd
            )
        return output

    def terminate(self) -> typing.Tuple[int, str]:
        """
        Wait for the command to end.

        :returns: A tuple of return code and remaining output.
        :rtype: tuple(int, str)
        """
        assert self._proxy_alive, "Attempting to terminate multiple times"

        self._c = self._c2
        try:
            next(self._cmd_context)
        except StopIteration as s:
            retval = typing.cast(typing.Tuple[int, str], s.args[0])
            assert isinstance(retval, tuple), "generator returned wrong type"
        else:
            raise RuntimeError("runctx generator didn't stop")

        self._proxy_alive = False
        self._c = CommandEndedChannel()

        return retval

    def _pre_terminate(self) -> None:
        """
        Mark the command as terminated.

        This is useful when a runctx detected that a command exited prematurely.
        """
        self._c = CommandEndedChannel()

    def _assert_end(self) -> None:
        """Ensure that this proxy was properly terminated."""
        if self._proxy_alive:
            raise RuntimeError(
                "A run-command proxy needs to be terminated before leaving its context!"
            )


class CommandEndedException(
    channel.DeathStringException, channel.ChannelTakenException
):
    """
    The command which was run (interactively) ended prematurely.

    This exception might be raised when reading from (or writing to) a
    :py:class:`~tbot.machine.linux.RunCommandProxy` and the remote command
    exited during the call.  You can catch the exception but after receiving
    it, no more interaction with the command is allowed except the final
    :py:meth:`~RunCommandProxy.terminate0` or
    :py:meth:`~RunCommandProxy.terminate`.

    **Example**:

    .. code-block:: python

        with lh.run("foo", "command") as foo:
            try:
                while True:
                    foo.read_until_prompt("$ ")
                    foo.sendline("echo some command")
            except linux.CommandEndedException:
                pass

            foo.terminate0()
    """

    def __str__(self) -> str:
        return "Interactive command ended while attempting to interact with it."


class CommandEndedChannel(channel.channel.ChannelTaken):
    exception = CommandEndedException
