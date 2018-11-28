# tbot, Embedded Automation Tool
# Copyright (C) 2018  Harald Seiler
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

import time
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


def tbot_end(success: bool) -> None:
    log.message(
        log.c(
            log.u(
                "────────────────────────────────────────",
                "----------------------------------------",
            )
        ).dark
    )

    if log.LOGFILE is not None:
        log.message(f"Log written to {log.LOGFILE.name!r}")

    msg = log.c("SUCCESS").green.bold if success else log.c("FAILURE").red.bold
    duration = time.monotonic() - log.START_TIME
    log.EventIO(
        ["tbot", "end"],
        msg + f" ({duration:.3f}s)",
        nest_first=log.u("└─", "\\-"),
        verbosity=log.Verbosity.QUIET,
        success=success,
        duration=duration,
    )
