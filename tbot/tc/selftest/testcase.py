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
from tbot.machine import linux, board
from . import board_machine

__all__ = ("selftest_with_lab", "selftest_with_uboot", "selftest_with_linux")


class SubstituteBoard(typing.ContextManager[None]):
    __slots__ = ("board_orig", "uboot_orig", "linux_orig")

    def __enter__(self) -> None:
        self.board_orig = getattr(tbot.selectable, "Board")
        self.uboot_orig = getattr(tbot.selectable, "UBootMachine")
        self.linux_orig = getattr(tbot.selectable, "LinuxMachine")

        setattr(tbot.selectable, "Board", board_machine.TestBoard)
        setattr(tbot.selectable, "UBootMachine", board_machine.TestBoardUBoot)
        setattr(tbot.selectable, "LinuxMachine", board_machine.TestBoardLinuxUB)

    def __exit__(self, exc_type, exc_value, traceback) -> None:  # type: ignore
        setattr(tbot.selectable, "Board", self.board_orig)
        setattr(tbot.selectable, "UBootMachine", self.uboot_orig)
        setattr(tbot.selectable, "LinuxMachine", self.linux_orig)


@tbot.testcase
@tbot.with_lab
def selftest_decorated_lab(lh: linux.Lab) -> None:
    lh.exec0("uname", "-a")


@tbot.testcase
def selftest_with_lab(lab: typing.Optional[linux.Lab] = None) -> None:
    """Test the tbot.with_lab decorator."""
    with lab or tbot.acquire_lab() as lh:
        # Call without parameter
        selftest_decorated_lab()

        # Call with parameter
        selftest_decorated_lab(lh)


@tbot.testcase
@tbot.with_uboot
def selftest_decorated_uboot(ub: board.UBootMachine) -> None:
    ub.exec0("version")


@tbot.testcase
def selftest_with_uboot(lab: typing.Optional[tbot.selectable.LabHost] = None) -> None:
    """Test the tbot.with_uboot decorator."""
    with lab or tbot.acquire_lab() as lh:
        with SubstituteBoard():
            # Call without anything
            selftest_decorated_uboot()

            # Call with labhost
            selftest_decorated_uboot(lh)

            # Call with U-Boot
            with tbot.acquire_board(lh) as b:
                with tbot.acquire_uboot(b) as ub:
                    selftest_decorated_uboot(ub)


@tbot.testcase
@tbot.with_linux
def selftest_decorated_linux(lnx: linux.LinuxShell) -> None:
    lnx.exec0("uname", "-a")


@tbot.testcase
def selftest_with_linux(lab: typing.Optional[tbot.selectable.LabHost] = None) -> None:
    """Test the tbot.with_linux decorator."""
    with lab or tbot.acquire_lab() as lh:
        with SubstituteBoard():
            # Call without anything
            selftest_decorated_linux()

            # Call with labhost
            selftest_decorated_linux(lh)

            # Call with Linux
            with tbot.acquire_board(lh) as b:
                with tbot.acquire_linux(b) as lnx:
                    selftest_decorated_linux(lnx)
