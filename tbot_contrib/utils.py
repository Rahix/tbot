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

    .. versionadded:: 0.8.3
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
_ANSI_ESCAPE = re.compile(
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

    .. versionadded:: 0.9.2
    """
    return _ANSI_ESCAPE.sub("", s)


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

    .. versionadded:: 0.8.3
    .. versionchanged:: 0.9.2

        Fixed ``find_ip_address()`` not working properly when the route target
        is a local address.
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
                r"(?:local\s+)?\S+\s+(?:via\s+\S+\s+)?dev\s+\S+\s+src\s+(\S+).*",
                output,
                re.DOTALL,
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
    Compare the hashsum of two files (potentially from different hosts).

    ``hashcmp()`` automatically selects a hash-summing tool which is available
    on both hosts and uses it to compare the checksum of the two files.  It
    returns ``True`` if they match and ``False`` otherwise.  If one of the
    files does not exist, ``False`` is returned.

    .. versionadded:: 0.9.2
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


# alias for later functions which have a shadowing argument
_hashcmp = hashcmp


H1 = typing.TypeVar("H1", bound=linux.LinuxShell)
H2 = typing.TypeVar("H2", bound=linux.LinuxShell)


@typing.overload
def copy_to_dir(
    sources: linux.Path[H1],
    dest_dir: linux.Path[H2],
    *,
    hashcmp: bool = False,
) -> linux.Path[H2]:
    pass


@typing.overload
def copy_to_dir(
    sources: typing.Iterable[linux.Path[H1]],
    dest_dir: linux.Path[H2],
    *,
    hashcmp: bool = False,
) -> typing.List[linux.Path[H2]]:
    pass


def copy_to_dir(
    sources: typing.Union[linux.Path[H1], typing.Iterable[linux.Path[H1]]],
    dest_dir: linux.Path[H2],
    *,
    hashcmp: bool = False,
) -> typing.Union[linux.Path[H2], typing.List[linux.Path[H2]]]:
    """
    Copy one or more files to a directory

    This function will copy each file from ``sources`` into a new file in
    ``dest_dir`` which has the same name as the original one.

    This function uses :py:func:`linux.copy() <tbot.machine.linux.copy>` under
    the hood so ``sources`` and ``dest_dir`` need not be on the same host.  See
    that function for details.

    :param sources: The file(s) to copy.  This may be a single
        :py:class:`~tbot.machine.linux.Path` or an iterable which yields zero
        or more :py:class:`~tbot.machine.linux.Path` objects.

    :param linux.Path dest_dir: The target directory where the files should be
        copied to.  It does not need to be on the same host as ``sources``.

    :param bool hashcmp: This optional named argument can be set to true to
        make the function verify checksums of each file before performing the
        copy. This is very useful to skip superfluous copying operations.

    :returns: If a single ``sources`` path was passed, a single path is
        returned which points to the newly created copy.  If multiple
        ``sources`` were passed (as an iterable), a list of paths for each
        copied file is returned.

    **Example**: Copy a file from lab-host to a tftp-server for serving it to a
    target device.

    .. code-block:: python

        from tbot_contrib import utils

        linux_sources = lh.workdir / "linux"

        tftp_zimage = utils.copy_to_dir(
            linux_sources / "arch/arm/boot/zImage",
            tftp_server.tftp_dir,
            hashcmp=True,
        )

        tftp_filename = tftp_zimage.name

        u_boot.exec0("tftp", "0x10000000", f"{tftp_server.addr}:{tftp_filename}")

    **Example**: Copy many files from lab-host to a tftp-server for serving
    them to a target device.

    .. code-block:: python

        from tbot_contrib import utils

        linux_sources = lh.workdir / "linux"

        utils.copy_to_dir(
            [
                linux_sources / "arch/arm/boot/zImage",
                linux_sources / "arch/arm/boot/dts/mydevice.dtb",
            ],
            tftp_server.tftp_dir,
            hashcmp=True,
        )

    **Example**: Copy all config files to a new directory and then run a
    replacement command on each one.

    .. code-block:: python

        from tbot_contrib import utils

        config_dir = lnx.fsroot / "etc" / "myapp"
        newconfig_dir = lnx.workdir / "newconfig"
        lnx.exec0("rm", "-rf", newconfig_dir)
        lnx.exec0("mkdir", newconfig_dir)

        new_cfg_files = utils.copy_to_dir(
            config_dir.glob("*.conf"),
            newconfig_dir,
        )

        for cfg_file in new_cfg_files:
            lnx.exec0("sed", "-i", "s/eth0/wlan0/g", cfg_file)
    """
    if isinstance(sources, linux.Path):
        source_iter: typing.Iterable[linux.Path[H1]] = (sources,)
    else:
        source_iter = sources

    dest_list = []
    for source in source_iter:
        dest = dest_dir / source.name
        dest_list.append(dest)

        if hashcmp:
            if not _hashcmp(source, dest):
                linux.copy(source, dest)
        else:
            linux.copy(source, dest)

    if isinstance(sources, linux.Path):
        return dest_list[0]
    else:
        return dest_list
