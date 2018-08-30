import typing
import sys
import io
import itertools
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


NESTING = 0
INTERACTIVE = False


class EventIO(io.StringIO):
    """Stream for a log event."""

    def __init__(
        self,
        initial: typing.Union[str, c, None] = None,
        *,
        nest_first: typing.Optional[str] = None,
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
        # TODO: Write Log Event
        super().close()

    def __del__(self) -> None:
        if not self.closed:
            self.close()


def testcase_begin(name: str) -> None:
    """
    Log a testcase's beginning.

    :param str name: Name of the testcase
    """
    global NESTING

    EventIO("Calling " + c(name).cyan.bold + " ...")
    NESTING += 1


def testcase_end(success: bool = True) -> None:
    """
    Log a testcase's end.

    :param bool success: Whether the testcase succeeded
    """
    global NESTING

    if success:
        success_string = c("Done").green.bold
    else:
        success_string = c("Fail").red.bold

    EventIO(success_string + ".", nest_first=u("└─", "\\-"))
    NESTING -= 1


def command(mach: str, cmd: str) -> EventIO:
    """
    Log a command's execution.

    :param str mach: Name of the machine the command is run on
    :param str cmd: The command itself
    :rtype: EventIO
    :returns: A stream that the output of the command should
        be written to.
    """
    ev = EventIO("[" + c(mach).yellow + "] " + c(cmd).dark)
    ev.prefix = "   ## "

    if INTERACTIVE:
        if input(c("OK [Y/n]? ").magenta).upper() not in ("", "Y"):
            raise RuntimeError("Aborted by user")

    return ev


def message(msg: typing.Union[str, c]) -> EventIO:
    """
    Log a message.

    :param str msg: The message
    """
    return EventIO(msg)
