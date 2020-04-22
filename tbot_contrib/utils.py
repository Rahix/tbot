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

from tbot.machine import linux
import typing


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
