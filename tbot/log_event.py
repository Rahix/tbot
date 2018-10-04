from tbot import log
from tbot.log import u, c

__all__ = ("testcase_begin", "testcase_end", "command")


def testcase_begin(name: str) -> None:
    """
    Log a testcase's beginning.

    :param str name: Name of the testcase
    """
    log.EventIO(
        ["tc", "begin"],
        "Calling " + c(name).cyan.bold + " ...",
        verbosity=log.Verbosity.QUIET,
        name=name,
    )
    log.NESTING += 1


def testcase_end(name: str, duration: float, success: bool = True) -> None:
    """
    Log a testcase's end.

    :param float duration: Time passed while this testcase ran
    :param bool success: Whether the testcase succeeded
    """
    if success:
        success_string = c("Done").green.bold
    else:
        success_string = c("Fail").red.bold

    log.EventIO(
        ["tc", "end"],
        success_string + f". ({duration:.3f}s)",
        nest_first=u("└─", "\\-"),
        verbosity=log.Verbosity.QUIET,
        name=name,
        duration=duration,
        success=success,
    )
    log.NESTING -= 1


def command(mach: str, cmd: str) -> log.EventIO:
    """
    Log a command's execution.

    :param str mach: Name of the machine the command is run on
    :param str cmd: The command itself
    :rtype: EventIO
    :returns: A stream that the output of the command should
        be written to.
    """
    ev = log.EventIO(
        ["cmd", mach],
        "[" + c(mach).yellow + "] " + c(cmd).dark,
        verbosity=log.Verbosity.COMMAND,
        cmd=cmd,
    )
    ev.prefix = "   ## "

    if log.INTERACTIVE:
        if input(c("OK [Y/n]? ").magenta).upper() not in ("", "Y"):
            raise RuntimeError("Aborted by user")

    ev.verbosity = log.Verbosity.STDOUT
    return ev
