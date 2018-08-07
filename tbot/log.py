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


def _nest(after: str = u("├─", "+-")) -> str:
    return str(c("".join(itertools.repeat(u("│   ", "|   "), NESTING)) + after).dark)


class EventIO(io.StringIO):
    def __init__(self, initial: typing.Optional[str] = None) -> None:
        super().__init__("")

        self.cursor = 0
        self.first = True
        self.prefix: typing.Optional[str] = None

        if initial:
            self.writeln(initial)

    def _print_lines(self, last: bool = False) -> None:
        buf = self.getvalue()[self.cursor:]

        prefix = self.prefix or ""
        nest_first = _nest() + prefix
        nest_def = _nest(u("│ ", "| ")) + prefix
        while "\n" in buf:
            nest = nest_first if self.first else nest_def
            line = buf.split("\n", maxsplit=1)[0]
            print(nest + line)
            length = len(line) + 1
            self.cursor += length
            buf = buf[length:]
            self.first = False

        if last and buf != "":
            print(nest_def + buf)

    def writeln(self, s: str) -> int:
        return self.write(s + "\n")

    def write(self, s: str) -> int:
        res = super().write(s)

        self._print_lines()

        return res

    def close(self) -> None:
        self._print_lines(last=True)
        # TODO: Write Log Event
        super().close()


def testcase_begin(name: str) -> None:
    global NESTING

    print(_nest() + "Calling " + c(name).cyan.bold + " ...")
    NESTING += 1


def testcase_end(success: bool = True) -> None:
    global NESTING

    if success:
        success_string = c("Done").green.bold
    else:
        success_string = c("Fail").red.bold

    print(_nest(u("└─", "\\-")) + success_string + ".")
    NESTING -= 1


def command(mach: str, cmd: str) -> EventIO:
    ev = EventIO("[" + c(mach).yellow + "] " + c(cmd).dark)
    ev.prefix = "   ## "

    return ev


def message(msg: str) -> None:
    print(_nest() + msg)
