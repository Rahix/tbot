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
import enum
import io
import itertools
import json
import os
import re
import sys
import time
import typing

import termcolor2

IS_UNICODE = sys.stdout.encoding.upper() == "UTF-8"
IS_COLOR = False

# Taken from https://bixense.com/clicolors/
if (os.getenv("CLICOLOR", "1") != "0" and sys.stdout.isatty()) or os.getenv(
    "CLICOLOR_FORCE", "0"
) != "0":
    IS_COLOR = True


def u(with_unicode: str, without_unicode: str) -> str:
    """
    Select a string depending on whether the terminal supports unicode.

    :param str with_unicode: The string to be used if unicode is available
    :param str without_unicode: The string to be used if unicode is **not** available
    :rtype: str
    :returns: The selected string
    """
    if IS_UNICODE:
        return with_unicode
    return without_unicode


class _C(termcolor2._C):
    def __str__(self) -> str:
        if IS_COLOR:
            return super().__str__()
        else:
            return self.string


c = _C
_TC = typing.Union[_C, termcolor2._C]


@enum.unique
class Verbosity(enum.IntEnum):
    """Verbosity levels."""

    QUIET = 0
    INFO = enum.auto()
    COMMAND = enum.auto()
    STDOUT = enum.auto()
    CHANNEL = enum.auto()

    def __str__(self) -> str:
        return super(Verbosity, self).__str__().split(".")[-1]


NESTING = -1
INTERACTIVE = False
VERBOSITY = Verbosity.COMMAND
LOGFILE: typing.Optional[typing.TextIO] = None
START_TIME = time.monotonic()

_SPLIT_PATTERN = re.compile("(\r|\n)")


@contextlib.contextmanager
def with_verbosity(
    verbosity: Verbosity, *, nesting: typing.Optional[int] = None
) -> typing.Iterator[None]:
    """
    Temporarily change the verbosity to a different level.

    **Example**:

    .. code-block:: python

        # This command produces a lot of uninteresting output so let's reduce
        # verbosity while running it:
        with tbot.log.with_verbosity(tbot.log.Verbosity.COMMAND):
            kernel_log = lnx.exec0("dmesg")

    .. versionadded:: UNRELEASED
    """

    global VERBOSITY
    global NESTING

    old_verbosity = VERBOSITY
    old_nesting = NESTING

    try:
        VERBOSITY = verbosity
        if nesting is not None:
            NESTING = nesting

        yield None
    finally:
        VERBOSITY = old_verbosity
        if nesting is not None:
            NESTING = old_nesting


class EventIO(io.StringIO):
    """Stream for a log event."""

    def __init__(
        self,
        ty: typing.List[str],
        message: typing.Union[str, _TC],
        *,
        verbosity: Verbosity = Verbosity.INFO,
        nest_first: typing.Optional[str] = None,
        **kwargs: typing.Any,
    ) -> None:
        """
        Create a log event.

        A log event is a :class:`io.StringIO` and everything written to
        the stream will be added to the log event.

        :param str message: First line of the log event (the log message).  If
            the message contains newlines, only the first line will be printed as
            the message and the rest will be added to the log-event.
        """
        super().__init__("")

        self.cursor = 0
        self.prefix: typing.Optional[str] = None
        self.verbosity = verbosity
        self.ty = ty
        self.data = kwargs
        self._nextline = True

        msg = str(message).split("\n", 1)
        if self.verbosity <= VERBOSITY:
            print(self._prefix(nest_first or u("├─", "+-")) + msg[0])
        if len(msg) > 1:
            self.writeln(msg[1])

    def _prefix(self, nest_first: typing.Optional[str] = None) -> str:
        if NESTING == -1:
            return ""

        after = nest_first if nest_first is not None else u("│ ", "| ")
        prefix: str = self.prefix or ""
        return (
            str(c("".join(itertools.repeat(u("│   ", "|   "), NESTING)) + after).dark)
            + prefix
        )

    def _print_stdout(self, last: bool = False) -> None:
        buf = self.getvalue()[self.cursor :]

        if self.verbosity > VERBOSITY:
            return

        for fragment in (f for f in _SPLIT_PATTERN.split(buf) if f != ""):
            if self._nextline:
                sys.stdout.write(self._prefix() + c(""))
                self._nextline = False

            if fragment in ["\r", "\n"]:
                self._nextline = True

            sys.stdout.write(fragment)

        if last and not self._nextline:
            sys.stdout.write("\n")
            self._nextline = True

        self.cursor += len(buf)
        sys.stdout.flush()

    def writeln(self, s: typing.Union[str, _TC]) -> int:
        """Add a line to this log event."""
        return self.write(s + "\n")

    def write(self, s: str) -> int:
        r"""
        Add some text to this log event.

        Printing to stdout will only occur once a newline ``"\n"`` is
        written.
        """

        s = (
            s.replace("\x1B[H", "")
            .replace("\x1B[999;999H", "")
            .replace("\x1B[6n", "")
            .replace("\x1B[2J", "")
            .replace("\x1B[r", "")
            .replace("\x1B[u", "")
            .replace("\x1B7", "")
            .replace("\r\n", "\n")
            .replace("\n\r", "\n")
        )

        res = super().write(s)

        self._print_stdout()

        return res

    def __enter__(self) -> "EventIO":
        return self

    def close(self) -> None:
        """
        Finalize this log event.

        No more text can be added to this log event after
        closing it.
        """
        self._print_stdout(last=True)

        if LOGFILE is not None:
            ev = {
                "type": self.ty,
                "time": time.monotonic() - START_TIME,
                "data": self.data,
            }

            json.dump(ev, LOGFILE, indent=2)
            LOGFILE.write("\n")
            LOGFILE.flush()

        super().close()

    def __del__(self) -> None:
        if not self.closed:
            self.close()


def message(
    msg: typing.Union[str, _TC], verbosity: Verbosity = Verbosity.INFO
) -> EventIO:
    """
    Log a message.

    :param str msg: The message
    :param Verbosity verbosity: Message verbosity
    """
    return EventIO(["msg", str(verbosity)], msg, verbosity=verbosity, text=str(msg))


def warning(msg: typing.Union[str, _TC]) -> EventIO:
    """
    Emit a warning message.

    :param str msg: The message

    .. versionadded:: 0.6.3
    """
    return message(c("Warning").yellow.bold + ": " + msg, Verbosity.QUIET)


def skip(what: typing.Union[str, _TC]) -> EventIO:
    """
    Emit a testcase skip message.

    :param str what: What test is being skipped

    .. deprecated:: 0.8

        Use :py:func:`tbot.skip` instead.
    """
    warning("tbot.log.skip() is deprecated.  Use tbot.skip() instead.")
    return message(c("Skip").yellow.bold + " " + what, Verbosity.INFO)
