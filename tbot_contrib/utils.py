# tbot, Embedded Automation Tool
# Copyright (C) 2020  Heiko Schocher
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
import re
import typing

from tbot.machine import linux
from tbot.tc import shell


_SERVICES_CACHE: typing.Dict[str, typing.Dict[str, bool]] = {}


def ensure_sd_unit(lnx: linux.LinuxShell, services: typing.List[str]) -> None:
    """
    check if all systemd services in list services run on linux machine lnx.
    If not, try to start them.

    :param lnx: linux shell
    :param services: list of systemd services
    """
    if lnx.name not in _SERVICES_CACHE:
        _SERVICES_CACHE[lnx.name] = {}

    for s in services:
        if s in _SERVICES_CACHE[lnx.name]:
            continue

        if not lnx.test("systemctl", "is-active", s):
            lnx.exec0("sudo", "systemctl", "start", s)

        _SERVICES_CACHE[lnx.name][s] = True


# 7-bit C1 ANSI sequences, see https://stackoverflow.com/a/14693789
ANSI_ESCAPE = re.compile(
    r"""
    \x1B  # ESC
    (?:   # 7-bit C1 Fe (except CSI)
        [@-Z\\-_]
    |     # or [ for CSI, followed by a control sequence
        \[
        [0-?]*  # Parameter bytes
        [ -/]*  # Intermediate bytes
        [@-~]   # Final byte
    )
""",
    re.VERBOSE,
)


def strip_ansi_escapes(s: str) -> str:
    """
    Strip all ANSI escape sequences from a string

    This helper can be used when programs have colored output and piping with
    ``| cat`` doesn't help (e.g. forced color as with ``--color=always``).
    """
    return ANSI_ESCAPE.sub("", s)


_IP_CACHE: typing.Dict[typing.Tuple[linux.LinuxShell, str], str] = {}


def find_ip_address(
    lnx: linux.LinuxShell,
    route_target: typing.Optional[str] = None,
    force: bool = False,
) -> str:
    """
    Find out an IP-address of a host.

    In times where most hosts have many IP addresses, this is not as trivial as
    one would like.  This testcase approaches the problem by trying to find the
    IP-address, the host would use on a certain route.

    By default, this is the route to reach a theoretical host at ``1.0.0.0``.
    This will yield a sensible result in *most* cases but of course will not
    always be the address you want.  For more fine-grained control you can pass
    a ``route_target``.  This is the IP-address of this theoretical host to reach.

    :param linux.LinuxShell lnx: The host to work on.
    :param str route_target: An optional route target.  Defaults to ``1.0.0.0``.
    :param bool force: By default, this testcase caches results for faster
        lookup when called multiple times.  This parameter enforces a re-check
        which might be useful when the network configuration on ``lnx``
        changed.
    :rtype: str
    :returns: The IP-address which was found.
    """
    if route_target is None:
        # 1 equals to 1.0.0.0 which will probably yield a sensible route in
        # most cases.
        route_target = "1"

    if (lnx, route_target) not in _IP_CACHE:
        if shell.check_for_tool(lnx, "ip"):
            output = strip_ansi_escapes(
                lnx.exec0("ip", "route", "get", route_target, linux.Pipe, "cat")
            )
            match = re.match(
                r"\S+ (?:via \S+ )?dev \S+ src (\S+).*", output, re.DOTALL,
            )
            assert match is not None, f"Failed to parse `ip route` output ({output!r})!"
            ip = match.group(1)
        else:
            raise NotImplementedError("Found no way to find out ip-address")

        _IP_CACHE[(lnx, route_target)] = ip

    return _IP_CACHE[(lnx, route_target)]


_HASHCMP_TOOLS = [
    "sha256sum",
    "sha1sum",
    "md5sum",
    "crc32",
]


def hashcmp(a: linux.Path, b: linux.Path) -> bool:
    """
    Compare the hashsum of two files on (potentially different hosts).

    ``hashcmp()`` automatically selects a hash-summing tool which is available
    on both hosts and uses it to compare the checksum of the two files.  It
    returns ``True`` if they match and ``False`` otherwise.
    """
    if not a.exists() or not b.exists():
        # Short-circuit if one of the files is missing.
        return False

    for tool in _HASHCMP_TOOLS:
        if shell.check_for_tool(a.host, tool) and shell.check_for_tool(b.host, tool):
            break
    else:
        raise Exception("No suitable hashing tool found which exists on both hosts!")

    sum_a: str = a.host.exec0(tool, a).split()[0]
    sum_b: str = b.host.exec0(tool, b).split()[0]

    return sum_a == sum_b
