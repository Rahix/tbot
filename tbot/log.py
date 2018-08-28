import typing
import sys
import io
import itertools
from termcolor2 import c


def u(with_unicode: str, without_unicode: str) -> str:
    if sys.stdout.encoding == "UTF-8":
        return with_unicode
    return without_unicode


NESTING = 0
INTERACTIVE = False


class EventIO(io.StringIO):

    def __init__(
        self,
        initial: typing.Union[str, c, None] = None,
        *,
        nest_first: typing.Optional[str] = None,
    ) -> None:
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
        return self.write(s + "\n")

    def write(self, s: str) -> int:
        res = super().write(s)

        self._print_lines()

        return res

    def __enter__(self) -> "EventIO":
        return self

    def close(self) -> None:
        self._print_lines(last=True)
        # TODO: Write Log Event
        super().close()

    def __del__(self) -> None:
        if not self.closed:
            self.close()


def testcase_begin(name: str) -> None:
    global NESTING

    EventIO("Calling " + c(name).cyan.bold + " ...")
    NESTING += 1


def testcase_end(success: bool = True) -> None:
    global NESTING

    if success:
        success_string = c("Done").green.bold
    else:
        success_string = c("Fail").red.bold

    EventIO(success_string + ".", nest_first=u("└─", "\\-"))
    NESTING -= 1


def command(mach: str, cmd: str) -> EventIO:
    ev = EventIO("[" + c(mach).yellow + "] " + c(cmd).dark)
    ev.prefix = "   ## "

    if INTERACTIVE:
        if input(c("OK [Y/n]? ").magenta).upper() not in ("", "Y"):
            raise RuntimeError("Aborted by user")

    return ev


def message(msg: str) -> EventIO:
    return EventIO(msg)
