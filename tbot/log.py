import sys
import itertools
from termcolor2 import c


def u(with_unicode: str, without_unicode: str) -> str:
    if sys.stdout.encoding == "UTF-8":
        return with_unicode
    return without_unicode


NESTING = 0


def _nest(after: str = u("├─", "+-")) -> str:
    return str(c("".join(itertools.repeat(u("│   ", "|   "), NESTING)) + after).dark)


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


def command(mach: str, cmd: str) -> None:
    print(_nest() + "[" + c(mach).yellow + "] " + c(cmd).dark)


def message(msg: str) -> None:
    print(_nest() + msg)
