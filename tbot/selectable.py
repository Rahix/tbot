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
import contextlib
from typing import Any, Callable, Iterator

import tbot
from tbot.machine import connector, linux, board


class LocalLabHost(
    connector.SubprocessConnector, linux.Bash, linux.Lab, typing.ContextManager
):
    name = "local"


LabHost = LocalLabHost


@contextlib.contextmanager
def _inject_into_context(
    ctx: "tbot.Context", role: Callable[..., "tbot.role.Role"], instance: Any
) -> Iterator:
    did_register = False
    did_inject = False

    try:
        if role not in ctx._roles:
            ctx.register(type(instance), role)
            did_register = True

        manager = ctx._instances[type(instance)]
        if not manager.is_alive():
            manager.init(instance=instance)
            did_inject = True

        yield None
    finally:
        if did_register:
            del ctx._roles[role]  # type: ignore

        # If only the outer context from the acquire_*() function and the one
        # from the instance manager is active any more, remove from context:
        if did_inject and instance._rc == 2:
            manager.teardown()


def acquire_lab() -> LabHost:
    """
    .. warning::

       This function is deprecated!  Use :py:data:`tbot.ctx` instead:

       .. code-block:: python

          @tbot.testcase
          def testcase_with_lab() -> None:
              with tbot.ctx.request(tbot.role.LabHost) as lh:
                  lh.exec0("uname", "-a")

    Acquire a new connection to the LabHost.

    If your lab-host is using a :class:`~tbot.machine.connector.ParamikoConnector`
    this will create a new ssh connection.

    You should call this function as little as possible, because it can be very slow.
    If possible, try to reuse the labhost. A recipe for doing so is

    .. code-block:: python

        import typing
        import tbot
        from tbot.machine import linux

        @tbot.testcase
        def my_testcase(
            lab: typing.Optional[linux.LinuxShell] = None,
        ) -> None:
            with lab or tbot.acquire_lab() as lh:
                # Your code goes here
                ...

    :rtype: tbot.selectable.LabHost

    .. versionchanged:: UNRELEASED

       This function is now officially deprecated in favor of the
       :ref:`context` mechanism.
    """
    if hasattr(LabHost, "_unselected"):
        raise NotImplementedError("Maybe you haven't set a lab?")

    @contextlib.contextmanager
    def _internal() -> Any:
        with LabHost() as lh, _inject_into_context(tbot.ctx, tbot.role.LabHost, lh):
            yield lh

    return _internal()  # type: ignore


def acquire_local() -> LocalLabHost:
    """
    .. warning::

       This function is deprecated!  Use :py:data:`tbot.ctx` instead:

       .. code-block:: python

          @tbot.testcase
          def testcase_with_local() -> None:
              with tbot.ctx.request(tbot.role.LocalHost) as lo:
                  lo.exec0("uname", "-a")

    Acquire a machine for the local host.

    Localhost machines are very cheap so they do not need to be shared
    like the others and you can create as many as you want.  One usecase
    might be copying test-results to you local machine after the run.

    **Example**:

    .. code-block:: python

        import tbot

        @tbot.testcase
        def my_testcase() -> None:
            with tbot.acquire_local() as lo:
                lo.exec0("id", "-un")
                # On local machines you can access tbot's working directory:
                tbot.log.message(f"CWD: {lo.workdir}")

    .. versionchanged:: UNRELEASED

       This function is now officially deprecated in favor of the
       :ref:`context` mechanism.
    """

    @contextlib.contextmanager
    def _internal() -> Any:
        with LocalLabHost() as lo:
            with _inject_into_context(tbot.ctx, tbot.role.LocalHost, lo):
                yield lo

    return _internal()  # type: ignore


class Board(board.Board):
    _unselected = True
    name = "dummy"

    def __init__(self, lh: linux.Lab) -> None:  # noqa: D107
        raise NotImplementedError("no board selected")


def acquire_board(lh: LabHost) -> Board:
    """
    .. warning::

       This function is deprecated!  Use :py:data:`tbot.ctx` instead:

       .. code-block:: python

          @tbot.testcase
          def testcase_with_board() -> None:
              with tbot.ctx.request(tbot.role.Board) as b:
                  b.interactive()

    Acquire the selected board.

    If configured properly, :py:func:`tbot.acquire_board` will power on the
    hardware and open a serial-console for the selected board.  Just by itself,
    this is not too useful, so you will usually follow it up immediately with a
    call to either :py:func:`tbot.acquire_uboot` or
    :py:func:`tbot.acquire_linux`.

    **Example**:

    .. code-block:: python

        with tbot.acquire_lab() as lh:
            lh.exec0("echo", "Foo")
            with tbot.acquire_board(lh) as b, tbot.acquire_uboot(b) as ub:
                ub.exec0("version")

    .. versionchanged:: UNRELEASED

       This function is now officially deprecated in favor of the
       :ref:`context` mechanism.
    """
    if hasattr(Board, "_unselected"):
        raise NotImplementedError("Maybe you haven't set a board?")

    @contextlib.contextmanager
    def _internal() -> Any:
        with Board(lh) as b:  # type: ignore
            with _inject_into_context(tbot.ctx, tbot.role.Board, b):
                yield b

    return _internal()  # type: ignore


class UBootMachine(board.UBootShell, typing.ContextManager):
    """Dummy type that will be replaced by the actual selected U-Boot machine at runtime."""

    _unselected = True

    def __init__(self, lab: LabHost, *args: typing.Any) -> None:
        raise NotImplementedError("no u-boot selected")


def acquire_uboot(board: Board, *args: typing.Any) -> UBootMachine:
    """
    .. warning::

       This function is deprecated!  Use :py:data:`tbot.ctx` instead:

       .. code-block:: python

          @tbot.testcase
          def testcase_with_uboot() -> None:
              with tbot.ctx.request(tbot.role.BoardUBoot) as ub:
                  ub.exec0("version")

    Acquire the selected board's U-Boot shell.

    As there can only be one instance of the selected board's :class:`UBootShell` at a time,
    your testcases should optionally take the :class:`UBootShell` as a
    parameter. The recipe looks like this:

    .. code-block:: python

        import contextlib
        import typing
        import tbot
        from tbot.machine import board


        @tbot.testcase
        def my_testcase(
            lab: typing.Optional[tbot.selectable.LabHost] = None,
            uboot: typing.Optional[board.UBootShell] = None,
        ) -> None:
            with contextlib.ExitStack() as cx:
                lh = cx.enter_context(lab or tbot.acquire_lab())
                if uboot is not None:
                    ub = uboot
                else:
                    b = cx.enter_context(tbot.acquire_board(lh))
                    ub = cx.enter_context(tbot.acquire_uboot(b))

                ...

    :rtype: tbot.selectable.UBootMachine

    .. versionchanged:: UNRELEASED

       This function is now officially deprecated in favor of the
       :ref:`context` mechanism.
    """
    if hasattr(UBootMachine, "_unselected"):
        raise NotImplementedError("Maybe you haven't set a board?")

    @contextlib.contextmanager
    def _internal() -> Any:
        with UBootMachine(board, *args) as ub:  # type: ignore
            with _inject_into_context(tbot.ctx, tbot.role.BoardUBoot, ub):
                yield ub

    return _internal()  # type: ignore


class LinuxMachine(board.LinuxBootLogin, linux.LinuxShell, typing.ContextManager):
    """Dummy type that will be replaced by the actual selected Linux machine at runtime."""

    _unselected = True

    def __init__(self, *args: typing.Any) -> None:  # noqa: D107
        raise NotImplementedError("This is a dummy Linux")


def acquire_linux(
    b: typing.Union[Board, UBootMachine], *args: typing.Any
) -> LinuxMachine:
    """
    .. warning::

       This function is deprecated!  Use :py:data:`tbot.ctx` instead:

       .. code-block:: python

          @tbot.testcase
          def testcase_with_linux() -> None:
              with tbot.ctx.request(tbot.role.BoardLinux) as lnx:
                  lnx.exec0("cat", "/etc/os-release")

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

    :rtype: tbot.machine.linux.LinuxShell

    .. versionchanged:: UNRELEASED

       This function is now officially deprecated in favor of the
       :ref:`context` mechanism.
    """
    if hasattr(LinuxMachine, "_unselected"):
        raise NotImplementedError("Maybe you haven't set a board?")

    @contextlib.contextmanager
    def _internal() -> Any:
        with LinuxMachine(b, *args) as lnx:  # type: ignore
            with _inject_into_context(tbot.ctx, tbot.role.BoardLinux, lnx):
                yield lnx

    return _internal()  # type: ignore
