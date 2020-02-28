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

import contextlib
import re
import typing

import tbot
from .. import shell, machine, channel
from ..linux import special


class UBootStartupEvent(tbot.log.EventIO):
    def __init__(self, ub: machine.Machine) -> None:
        self.ub = ub
        super().__init__(
            ["board", "uboot", ub.name],
            tbot.log.c("UBOOT").bold + f" ({ub.name})",
            verbosity=tbot.log.Verbosity.QUIET,
        )

        self.verbosity = tbot.log.Verbosity.STDOUT
        self.prefix = "   <> "

    def close(self) -> None:
        setattr(self.ub, "bootlog", self.getvalue())
        self.data["output"] = self.getvalue()
        super().close()


class UbootStartup(machine.Machine):
    _uboot_init_event: typing.Optional[tbot.log.EventIO] = None

    def _uboot_startup_event(self) -> tbot.log.EventIO:
        if self._uboot_init_event is None:
            self._uboot_init_event = UBootStartupEvent(self)

        return self._uboot_init_event


class UBootAutobootIntercept(machine.Initializer, UbootStartup):
    """
    Machine-initializer to intercept U-Boot autobooting.

    The default settings for this class should work for most cases, but if a
    custom autoboot prompt was configured, or a special key sequence is
    necessary, you will have to adjust this here.

    **Example**:

    .. code-block:: python

        class MyUBoot(
            board.Connector,
            board.UBootAutobootIntercept,
            board.UBootShell,
        ):
            autoboot_prompt = re.compile(b"Press DEL 4 times.{0,100}", re.DOTALL)
            autoboot_keys = "\\x7f\\x7f\\x7f\\x7f"
    """

    autoboot_prompt: typing.Optional[
        channel.channel.ConvenientSearchString
    ] = re.compile(b"autoboot:\\s{0,5}\\d{0,3}\\s{0,3}.{0,80}")
    """
    Autoboot prompt to wait for.
    """

    autoboot_keys: typing.Union[str, bytes] = "\r"
    """
    Keys to press as soon as autoboot prompt is detected.
    """

    @contextlib.contextmanager
    def _init_machine(self) -> typing.Iterator:
        if self.autoboot_prompt is not None:
            with self.ch.with_stream(self._uboot_startup_event()):
                self.ch.read_until_prompt(prompt=self.autoboot_prompt)
                self.ch.send(self.autoboot_keys)

        yield None


_hush_find_unsafe = re.compile(r"[^\w@%+=:,./-]", re.ASCII).search


def _hush_quote(s: str) -> str:
    if not s:
        return '""'
    if _hush_find_unsafe(s) is None:
        return s

    # - Quote \ (inside quotes) as \\
    # - Quote single quotes using a \ (outside the original quotes).
    #
    # Example: $'\b is quoted as '$'\''\\b'
    s = s.replace("\\", "\\\\").replace("'", "'\\''")
    return "'" + s + "'"


ArgTypes = typing.Union[str, special.Special]


class UBootShell(shell.Shell, UbootStartup):
    """
    U-Boot shell.

    The interface of this shell was designed to be close to the
    :ref:`Linux shell <linux-shells>` design.  This means that U-Boot shells
    also provide

    - :py:meth:`ub.escape() <tbot.machine.board.UBootShell.escape>` - Escape
      args for the U-Boot shell.
    - :py:meth:`ub.exec0() <tbot.machine.board.UBootShell.exec0>` - Run command
      and ensure it succeeded.
    - :py:meth:`ub.exec() <tbot.machine.board.UBootShell.exec>` - Run command
      and return output and return code.
    - :py:meth:`ub.test() <tbot.machine.board.UBootShell.test>` - Run command
      and return boolean whether it succeeded.
    - :py:meth:`ub.env() <tbot.machine.board.UBootShell.env>` - Get/Set
      environment variables.
    - :py:meth:`ub.interactive() <tbot.machine.board.UBootShell.interactive>` -
      Start an interactive session for this machine.

    There is also the special :py:meth:`ub.boot() <tbot.machine.board.UBootShell.boot>`
    which will boot a payload and return the machine's channel, for use in a
    machine for the booted payload.
    """

    prompt: typing.Union[str, bytes] = "U-Boot> "
    """
    Prompt which was configured for U-Boot.

    Commonly ``"U-Boot> "``, ``"=> "``, or ``"U-Boot# "``.

    .. warning::

        **Don't forget the trailing space, if your prompt has one!**
    """

    bootlog: str
    """Transcript of console output during boot."""

    @contextlib.contextmanager
    def _init_shell(self) -> typing.Iterator:
        with self._uboot_startup_event() as ev, self.ch.with_stream(ev):
            self.ch.prompt = (
                self.prompt.encode("utf-8")
                if isinstance(self.prompt, str)
                else self.prompt
            )

            while True:
                try:
                    self.ch.read_until_prompt(timeout=0.2)
                    break
                except TimeoutError:
                    self.ch.sendintr()

        yield None

    def escape(self, *args: ArgTypes) -> str:
        """Escape a string so it can be used safely on the U-Boot command-line."""
        string_args = []
        for arg in args:
            if isinstance(arg, str):
                # We can't use shlex.quote() here because U-Boot's shell of
                # course has its own rules for quoting ...
                string_args.append(_hush_quote(arg))
            elif isinstance(arg, special.Special):
                string_args.append(arg._to_string(self))
            else:
                raise TypeError(f"{type(arg)!r} is not a supported argument type!")

        return " ".join(string_args)

    def exec(self, *args: ArgTypes) -> typing.Tuple[int, str]:
        """
        Run a command in U-Boot.

        **Example**:

        .. code-block:: python

            retcode, output = ub.exec("version")
            assert retcode == 0

        :rtype: tuple(int, str)
        :returns: A tuple with the return code of the command and its console
            output.  The output will also contain a trailing newline in most
            cases.
        """
        cmd = self.escape(*args)

        with tbot.log_event.command(self.name, cmd) as ev:
            self.ch.sendline(cmd, read_back=True)
            with self.ch.with_stream(ev, show_prompt=False):
                out = self.ch.read_until_prompt()
            ev.data["stdout"] = out

            self.ch.sendline("echo $?", read_back=True)
            retcode = self.ch.read_until_prompt()

        return (int(retcode), out)

    def exec0(self, *args: ArgTypes) -> str:
        """
        Run a command and assert its return code to be 0.

        **Example**:

        .. code-block:: python

            output = ub.exec0("version")

            # This will raise an exception!
            ub.exec0("false")

        :rtype: str
        :returns: The command's console output.  It will also contain a trailing
            newline in most cases.
        """
        retcode, out = self.exec(*args)
        if retcode != 0:
            cmd = self.escape(*args)
            raise Exception(f"command {cmd!r} failed")
        return out

    def test(self, *args: ArgTypes) -> bool:
        """
        Run a command and return a boolean value whether it succeeded.

        **Example**:

        .. code-block:: python

            if ub.test("true"):
                tbot.log.message("Is correct")

        :rtype: bool
        :returns: Boolean representation of commands success.  ``True`` if
            return code was ``0``, ``False`` otherwise.
        """
        retcode, _ = self.exec(*args)
        return retcode == 0

    def env(self, var: str, value: typing.Optional[ArgTypes] = None) -> str:
        """
        Get or set an environment variable.

        **Example**:

        .. code-block:: python

            # Get the value of a var
            value = ub.env("bootcmd")

            # Set the value of a var
            lnx.env("bootargs", "loglevel=7")

        :param str var: Environment variable name.
        :param str value: Optional value to set the variable to.
        :rtype: str
        :returns: Current (new) value of the environment variable.
        """
        if value is not None:
            self.exec0("setenv", var, value)

        # Use `printenv var` instead of `echo "$var"` because some values would
        # otherwise result in broken expansion.
        output = self.exec0("printenv", var)

        # `output` contains "<varname>=<value>\n" so slice off the variable
        # name and trailing newline.
        return output[len(var) + 1 : -1]

    def boot(self, *args: ArgTypes) -> channel.Channel:
        """
        Boot a payload from U-Boot.

        This method will run the given command and expects it to start booting
        a payload.  ``ub.boot()`` will then return the channel so a new machine
        can be built ontop of it for the booted payload.

        **Example**:

        .. code-block:: python

            ub.env("bootargs", "loglevel=7")
            ch = ub.boot("bootm", "0x10000000")

        :rtype: tbot.machine.channel.Channel
        """
        cmd = self.escape(*args)

        with tbot.log_event.command(self.name, cmd):
            self.ch.sendline(cmd, read_back=True)

        return self.ch.take()

    def interactive(self) -> None:
        """
        Start an interactive session on this machine.

        This method will connect tbot's stdio to the machine's channel so you
        can interactively run commands.  This method is used by the
        ``interactive_uboot`` testcase.
        """
        tbot.log.message("Entering interactive shell (CTRL+D to exit) ...")

        # It is important to send a space before the newline.  Otherwise U-Boot
        # will reexecute the last command which we definitely do not want here.
        self.ch.sendline(" ")
        self.ch.attach_interactive()
        print("")
        self.ch.sendline(" ")

        try:
            self.ch.read_until_prompt(timeout=0.5)
        except TimeoutError:
            raise Exception("Failed to reacquire U-Boot after interactive session!")

        tbot.log.message("Exiting interactive shell ...")

    # Utilities ----- {{{
    _ram_base: int

    @property
    def ram_base(self) -> int:
        """
        Return the base address of RAM for this U-Boot instance.

        This address can be used as a safe bet when your testcase needs to
        store something in RAM.

        **Example**:

        .. code-block:: python

            serverip =  # ...
            filepath =  # ...
            ub.exec0("tftp", hex(ub.ram_base), f"{serverip}:{filepath}")
            ub.exec0("iminfo", hex(ub.ram_base))
        """
        import re

        try:
            return self._ram_base
        except AttributeError:
            out = self.exec0("bdinfo")
            match = re.search(r"^-> start\s+= (0x[\dA-Fa-f]+)$", out, re.MULTILINE)
            if match is None:
                raise Exception("RAM base not found in bdinfo output!")
            self._ram_base = int(match.group(1), 16)
            return self._ram_base

    # }}}
