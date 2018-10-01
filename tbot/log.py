import enum
import io
import itertools
import json
import sys
import time
import typing
from termcolor2 import c


def u(with_unicode: str, without_unicode: str) -> str:
    """
    Select a string depending on whether the terminal supports unicode.

    :param str with_unicode: The string to be used if unicode is available
    :param str without_unicode: The string to be used if unicode is **not** available
    :rtype: str
    :returns: The selected string
    """
    if sys.stdout.encoding == "UTF-8":
        return with_unicode
    return without_unicode


@enum.unique
class Verbosity(enum.IntEnum):
    """Verbosity levels."""

    QUIET = 0
    INFO = enum.auto()
    COMMAND = enum.auto()
    STDOUT = enum.auto()
    CHANNEL = enum.auto()


NESTING = 0
INTERACTIVE = False
VERBOSITY = Verbosity.INFO
LOGFILE: typing.Optional[typing.TextIO] = None
START_TIME = time.monotonic()


class EventIO(io.StringIO):
    """Stream for a log event."""

    def __init__(
        self,
        ty: typing.List[str],
        initial: typing.Union[str, c, None] = None,
        *,
        verbosity: Verbosity = Verbosity.INFO,
        nest_first: typing.Optional[str] = None,
        **kwargs: typing.Any,
    ) -> None:
        """
        Create a log event.

        A log event is a :class:`io.StringIO` and everything written to
        the stram will be added to the log event.

        :param str initial: Optional first line of the log event
        """
        super().__init__("")

        self.cursor = 0
        self.first = True
        self.prefix: typing.Optional[str] = None
        self.nest_first = nest_first or u("├─", "+-")
        self.verbosity = verbosity
        self.ty = ty
        self.data = kwargs

        if initial:
            self.writeln(str(initial))

    def _prefix(self) -> str:
        after = self.nest_first if self.first else u("│ ", "| ")
        self.first = False
        prefix: str = self.prefix or ""
        return (
            str(c("".join(itertools.repeat(u("│   ", "|   "), NESTING)) + after).dark)
            + prefix
        )

    def _print_lines(self, last: bool = False) -> None:
        buf = self.getvalue()[self.cursor :]

        if self.verbosity > VERBOSITY:
            return

        while "\n" in buf:
            line = buf.split("\n", maxsplit=1)[0]
            print(self._prefix() + line)
            length = len(line) + 1
            self.cursor += length
            buf = buf[length:]
            self.first = False

        if last and buf != "":
            print(self._prefix() + buf)

    def writeln(self, s: typing.Union[str, c]) -> int:
        """Add a line to this log event."""
        return self.write(s + "\n")

    def write(self, s: str) -> int:
        r"""
        Add some text to this log event.

        Printing to stdout will only occur once a newline ``"\n"`` is
        written.
        """
        res = super().write(s)

        self._print_lines()

        return res

    def __enter__(self) -> "EventIO":
        return self

    def close(self) -> None:
        """
        Finalize this log event.

        No more text can be added to this log event after
        closing it.
        """
        self._print_lines(last=True)

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
    msg: typing.Union[str, c], verbosity: Verbosity = Verbosity.INFO
) -> EventIO:
    """
    Log a message.

    :param str msg: The message
    :param Verbosity verbosity: Message verbosity
    """
    return EventIO(["msg"], msg, verbosity=verbosity, text=str(msg))
