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

import typing
from tbot.machine import connector, linux, board


class LocalLabHost(connector.SubprocessConnector, linux.Bash, typing.ContextManager):
    name = "local"


LabHost = LocalLabHost


def acquire_lab() -> LabHost:
    """
    Acquire a new connection to the LabHost.

    If your :class:`~tbot.machine.linux.LabHost` is a :class:`~tbot.machine.linux.lab.SSHLabHost`
    this will create a new ssh connection.

    You should call this function as little as possible, because it can be very slow.
    If possible, try to reuse the labhost. A recipe for doing so is::

        import typing
        import tbot
        from tbot.machine import linux

        @tbot.testcase
        def my_testcase(
            lab: typing.Optional[linux.LabHost] = None,
        ) -> None:
            with lab or tbot.acquire_lab() as lh:
                # Your code goes here
                ...

    :rtype: tbot.machine.linux.LabHost
    """
    if hasattr(LabHost, "_unselected"):
        raise NotImplementedError("Maybe you haven't set a lab?")
    return LabHost()


def acquire_local() -> LocalLabHost:
    """
    Acquire a machine for the local host.

    Localhost machines are very cheap so they do not need to be shared
    like the others and you can create as many as you want.  One usecase
    might be copying test-results to you local machine after the run.

    Example::

        import tbot

        @tbot.testcase
        def my_testcase() -> None:
            with tbot.acquire_local() as lo:
                lo.exec0("id", "-un")
                # On local machines you can access tbot's working directory:
                tbot.log.message(f"CWD: {lo.tbotdir}")
    """
    return LocalLabHost()


class Board(typing.ContextManager):
    """Board class is no longer implemented."""

    _unselected = True
    name = "dummy"

    def __init__(self, lh: linux.LabHost) -> None:  # noqa: D107
        raise NotImplementedError("`Board` is no longer implemented.")

    def poweron(self) -> None:  # noqa: D102
        raise NotImplementedError("`Board` is no longer implemented.")

    def poweroff(self) -> None:  # noqa: D102
        raise NotImplementedError("`Board` is no longer implemented.")


def acquire_board(lh: LabHost) -> typing.NoReturn:
    """No longer implemented."""
    raise NotImplementedError("acquire_board() is no longer implemented.")


class UBootMachine(board.UBootShell, typing.ContextManager):
    """Dummy type that will be replaced by the actual selected U-Boot machine at runtime."""

    _unselected = True

    def __init__(self, lab: LabHost, *args: typing.Any) -> None:
        raise NotImplementedError("no u-boot selected")


def acquire_uboot(lab: LabHost, *args: typing.Any) -> UBootMachine:
    """
    Acquire the board's U-Boot shell.

    As there can only be one instance of :class:`UBootMachine` at a time,
    your testcases should optionally take the :class:`UBootMachine` as a
    parameter. The recipe looks like this::

        import contextlib
        import typing
        import tbot
        from tbot.machine import board


        @tbot.testcase
        def my_testcase(
            lab: typing.Optional[tbot.selectable.LabHost] = None,
            uboot: typing.Optional[board.UBootMachine] = None,
        ) -> None:
            with contextlib.ExitStack() as cx:
                lh = cx.enter_context(lab or tbot.acquire_lab())
                if uboot is not None:
                    ub = uboot
                else:
                    b = cx.enter_context(tbot.acquire_board(lh))
                    ub = cx.enter_context(tbot.acquire_uboot(b))

                ...

    :rtype: tbot.machine.board.UBootMachine
    """
    if hasattr(UBootMachine, "_unselected"):
        raise NotImplementedError("Maybe you haven't set a board?")
    return UBootMachine(lab, *args)


class LinuxMachine(linux.LinuxShell, typing.ContextManager):
    """Dummy type that will be replaced by the actual selected Linux machine at runtime."""

    _unselected = True

    def __init__(self, *args: typing.Any) -> None:  # noqa: D107
        raise NotImplementedError("This is a dummy Linux")


def acquire_linux(
    b: typing.Union[LabHost, UBootMachine], *args: typing.Any
) -> LinuxMachine:
    """
    Acquire the board's Linux shell.

    Can either boot from a previously created U-Boot (if the implementation
    supports this) or directly.

    To write testcases that work both from the commandline and when called from other
    testcases, use the following recipe::

        import contextlib
        import typing
        import tbot
        from tbot.machine import board


        @tbot.testcase
        def test_testcase(
            lab: typing.Optional[tbot.selectable.LabHost] = None,
            board_linux: typing.Optional[board.LinuxMachine] = None,
        ) -> None:
            with contextlib.ExitStack() as cx:
                lh = cx.enter_context(lab or tbot.acquire_lab())
                if board_linux is not None:
                    lnx = board_linux
                else:
                    b = cx.enter_context(tbot.acquire_board(lh))
                    lnx = cx.enter_context(tbot.acquire_linux(b))

                ...

    :rtype: tbot.machine.board.LinuxMachine
    """
    if hasattr(LinuxMachine, "_unselected"):
        raise NotImplementedError("Maybe you haven't set a board?")
    return LinuxMachine(b, *args)
