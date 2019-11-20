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

import tbot
from selftest import *  # noqa
from tbot.tc.uboot import build as uboot_build  # noqa
from tbot.tc.uboot import checkout as uboot_checkout  # noqa


@tbot.testcase
def interactive_lab() -> None:
    """Start an interactive shell on the lab-host."""
    with tbot.acquire_lab() as lh:
        lh.interactive()


@tbot.testcase
def interactive_build() -> None:
    """Start an interactive shell on the build-host."""
    with tbot.acquire_lab() as lh:
        with lh.build() as bh:
            bh.exec0("cd", bh.workdir)
            bh.interactive()


@tbot.testcase
def interactive_board() -> None:
    """Start an interactive session on the selected boards serial console."""
    with tbot.acquire_lab() as lh:
        with tbot.acquire_board(lh) as b:
            b.interactive()


@tbot.testcase
def interactive_uboot() -> None:
    """Start an interactive U-Boot shell on the selected board."""
    with tbot.acquire_lab() as lh:
        with tbot.acquire_board(lh) as b, tbot.acquire_uboot(b) as ub:
            ub.interactive()


@tbot.testcase
def interactive_linux() -> None:
    """Start an interactive Linux shell on the selected board."""
    with tbot.acquire_lab() as lh:
        with tbot.acquire_board(lh) as b, tbot.acquire_linux(b) as lnx:
            lnx.interactive()
