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
import time
import typing

import tbot
from .. import shell, machine
from ..linux import special


class ZephyrStartupEvent(tbot.log.EventIO):
    def __init__(self, ze: machine.Machine) -> None:
        self.ze = ze
        super().__init__(
            ["board", "zephyr", ze.name],
            tbot.log.c("ZEPHYR").bold + f" ({ze.name})",
            verbosity=tbot.log.Verbosity.QUIET,
        )

        self.verbosity = tbot.log.Verbosity.STDOUT
        self.prefix = "   <> "

    def close(self) -> None:
        setattr(self.ze, "bootlog", self.getvalue())
        self.data["output"] = self.getvalue()
        super().close()


class ZephyrStartup(machine.Machine):
    _zephyr_init_event: typing.Optional[tbot.log.EventIO] = None
    _timeout_start: typing.Optional[float] = None

    boot_timeout: typing.Optional[float] = None
    """
    Maximum time from power-on to Zephyr shell.

    If tbot can't reach the Zephyr shell during this time, an exception will be thrown.
    """

    def _zephyr_startup_event(self) -> tbot.log.EventIO:
        if self._zephyr_init_event is None:
            self._zephyr_init_event = ZephyrStartupEvent(self)

            self._timeout_start = time.monotonic()

        return self._zephyr_init_event


ArgTypes = typing.Union[str, special.Special]


class ZephyrShell(shell.Shell, ZephyrStartup):
    """
    Zephyr shell.

    The interface of this shell is really simple. It provides

    - :py:meth:`ze.exec() <tbot.machine.board.ZephyrShell.exec>` - Run command
      and return output.
    - :py:meth:`ze.interactive() <tbot.machine.board.ZephyrShell.interactive>` -
      Start an interactive session for this machine.
    """

    prompt: typing.Union[str, bytes] = "shell> "
    """
    Prompt which was configured for Zephyr.

    Commonly ``"shell> "``.

    .. warning::

        **Don't forget the trailing space, if your prompt has one!**
    """

    bootlog: str
    """Transcript of console output during boot."""

    @contextlib.contextmanager
    def _init_shell(self) -> typing.Iterator:
        with self._zephyr_startup_event() as ev, self.ch.with_stream(ev):
            self.ch.prompt = (
                self.prompt.encode("utf-8")
                if isinstance(self.prompt, str)
                else self.prompt
            )

            # Set a blacklist of control characters.  These characters were
            # copied over from the U-Boot board.
            self.ch._write_blacklist = [
                0x00,  # NUL  | Null
                0x01,  # SOH  | Start of Heading
                0x02,  # STX  | Start of Text
                0x03,  # ETX  | End of Text / Interrupt
                0x04,  # EOT  | End of Transmission
                0x05,  # ENQ  | Enquiry
                0x06,  # ACK  | Acknowledge
                0x07,  # BEL  | Bell, Alert
                0x08,  # BS   | Backspace
                0x09,  # HT   | Character Tabulation, Horizontal Tabulation
                0x0B,  # VT   | Line Tabulation, Vertical Tabulation
                0x0C,  # FF   | Form Feed
                0x0E,  # SO   | Shift Out
                0x0F,  # SI   | Shift In
                0x10,  # DLE  | Data Link Escape
                0x11,  # DC1  | Device Control One (XON)
                0x12,  # DC2  | Device Control Two
                0x13,  # DC3  | Device Control Three (XOFF)
                0x14,  # DC4  | Device Control Four
                0x15,  # NAK  | Negative Acknowledge
                0x16,  # SYN  | Synchronous Idle
                0x17,  # ETB  | End of Transmission Block
                0x18,  # CAN  | Cancel
                0x1A,  # SUB  | Substitute / Suspend Process
                0x1B,  # ESC  | Escape
                0x1C,  # FS   | File Separator
                0x7F,  # DEL  | Delete
            ]

            while True:
                if self.boot_timeout is not None:
                    assert self._timeout_start is not None
                    if (time.monotonic() - self._timeout_start) > self.boot_timeout:
                        raise TimeoutError("Zephyr did not reach shell in time")
                try:
                    self.ch.read_until_prompt(timeout=0.2)
                    break
                except TimeoutError:
                    self.ch.sendintr()

        yield None

    def escape(self, *args: ArgTypes) -> str:
        """Escape a string so it can be used safely on the Zephyr command-line."""
        string_args = []
        for arg in args:
            if isinstance(arg, str):
                string_args.append(arg)
            elif isinstance(arg, special.Special):
                string_args.append(arg._to_string(self))
            else:
                raise TypeError(f"{type(arg)!r} is not a supported argument type!")

        return " ".join(string_args)

    def exec(self, *args: ArgTypes) -> str:
        """
        Run a command in Zephyr.

        **Example**:

        .. code-block:: python

            output = ze.exec("help")

        :rtype: str
        :returns: A str with the console output. The output will also contain a
                  trailing newline in most cases.
        """
        cmd = self.escape(*args)

        with tbot.log_event.command(self.name, cmd) as ev:
            self.ch.sendline(cmd, read_back=True)
            with self.ch.with_stream(ev, show_prompt=False):
                out = self.ch.read_until_prompt()
            ev.data["stdout"] = out

        return out

    def interactive(self) -> None:
        """
        Start an interactive session on this machine.

        This method will connect tbot's stdio to the machine's channel so you
        can interactively run commands.  This method is used by the
        ``interactive_zephyr`` testcase.
        """
        tbot.log.message(
            f"Entering interactive shell ({tbot.log.c('CTRL+D to exit').bold}) ..."
        )

        # Unlike U-Boot, I don't think Zephyr needs the space before the newline,
        # but it doesn't harm.
        self.ch.sendline(" ")
        self.ch.attach_interactive()
        print("")
        self.ch.sendline(" ")

        try:
            self.ch.read_until_prompt(timeout=0.5)
        except TimeoutError:
            raise Exception("Failed to reacquire Zephyr after interactive session!")

        tbot.log.message("Exiting interactive shell ...")
