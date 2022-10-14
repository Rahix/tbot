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

import typing

import tbot
from tbot.machine import linux

__all__ = ("check_for_tool", "copy")

H1 = typing.TypeVar("H1", bound=linux.LinuxShell)
H2 = typing.TypeVar("H2", bound=linux.LinuxShell)


@tbot.testcase
def copy(p1: linux.Path[H1], p2: linux.Path[H2]) -> None:
    """
    Copy a file, possibly from one host to another.

    .. versionchanged:: 0.10.2

        This function has been moved to :py:func:`tbot.machine.linux.copy`.
        Please read its documentation for more details.  The old name here is a
        compatibility alias.
    """
    return linux.copy(p1, p2)


_TOOL_CACHE: typing.Dict[linux.LinuxShell, typing.Dict[str, bool]] = {}


def check_for_tool(host: linux.LinuxShell, tool: str, force: bool = False) -> bool:
    """
    Check whether a certain tool/program is installed on a host.

    Results from previous invocations are cached.

    **Example**:

    .. code-block:: python

        if shell.check_for_tool(lh, "wget"):
            lh.exec0("wget", download_url, "-O", lh.workdir / "download.tgz")
        elif shell.check_for_tool(lh, "curl"):
            lh.exec0("curl", download_url, "-o", lh.workdir / "download.tgz")
        else:
            raise Exception("Need either 'wget' or 'curl'!")

    :param linux.LinuxShell host: The host to ceck on.
    :param str tool: Name of the binary to check for.
    :param bool force: Forces the check by not using the cache, default value is ``False``.
    :rtype: bool
    :returns: ``True`` if the tool was found and ``False`` otherwise.
    """
    if host not in _TOOL_CACHE:
        _TOOL_CACHE[host] = {}

    if force or tool not in _TOOL_CACHE[host]:
        with tbot.testcase("check_for_tool"):
            has_tool = host.test("which", tool)
            _TOOL_CACHE[host][tool] = has_tool

            if has_tool:
                tbot.log.message(
                    f"Host '{tbot.log.c(host.name).yellow}' has "
                    + f"'{tbot.log.c(tool).bold}' installed."
                )
            else:
                tbot.log.message(
                    f"Host '{tbot.log.c(host.name).yellow}' does "
                    + f"{tbot.log.c('not').red} have '{tbot.log.c(tool).bold}' installed."
                )

    return _TOOL_CACHE[host][tool]
