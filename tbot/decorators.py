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

import contextlib
import functools
import typing

import tbot
from tbot import selectable
from tbot.machine import linux, board

if typing.TYPE_CHECKING:
    import mypy_extensions as mypy
else:

    class mypy:
        class KwArg:
            def __new__(cls, ty: typing.Any) -> None:
                pass

        class VarArg:
            def __new__(cls, ty: typing.Any) -> None:
                pass

        class DefaultArg:
            def __new__(cls, ty: typing.Any, name: typing.Optional[str] = None) -> None:
                pass


__all__ = ("testcase", "with_lab", "with_zephyr", "with_uboot", "with_linux")

F_tc = typing.TypeVar("F_tc", bound=typing.Callable[..., typing.Any])


def testcase(tc: F_tc) -> F_tc:
    """
    Decorate a function to make it a testcase.

    **Example**::

        @tbot.testcase
        def foobar_testcase(x: str) -> int:
            return int(x, 16)
    """

    @functools.wraps(tc)
    def wrapped(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
        with tbot.testcase(tc.__name__):
            return tc(*args, **kwargs)

        # This line will only be reached when a testcase was skipped.
        # Return `None` as the placeholder return value.
        return None

    setattr(wrapped, "_tbot_testcase", tc.__name__)
    return typing.cast(F_tc, wrapped)


def named_testcase(name: str) -> typing.Callable[[F_tc], F_tc]:
    """
    Decorate a function to make it a testcase, but with a different name.

    The testcase's name is relevant for log-events and when calling
    it from the commandline.

    **Example**::

        @tbot.named_testcase("my_different_testcase")
        def foobar_testcase(x: str) -> int:
            return int(x, 16)

    (On the commandline you'll have to run ``tbot my_different_testcase`` now.)
    """

    def _named_testcase(tc: F_tc) -> F_tc:
        @functools.wraps(tc)
        def wrapped(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
            with tbot.testcase(name):
                return tc(*args, **kwargs)

            # This line will only be reached when a testcase was skipped.
            # Return `None` as the placeholder return value.
            return None

        setattr(wrapped, "_tbot_testcase", name)
        return typing.cast(F_tc, wrapped)

    return _named_testcase


F_lh = typing.TypeVar("F_lh", bound=typing.Callable[..., typing.Any])
F_lab = typing.Callable[
    [
        mypy.DefaultArg(typing.Optional[linux.Lab], "lab"),  # noqa: F821
        mypy.VarArg(typing.Any),
        mypy.KwArg(typing.Any),
    ],
    typing.Any,
]


def with_lab(tc: F_lh) -> F_lab:
    """
    Decorate a function to automatically supply the lab-host as an argument.

    The idea is that when using this decorator and calling the testcase
    without a lab-host, tbot will automatically acquire the default lab.

    **Example**::

        from tbot.machine import linux

        @tbot.testcase
        @tbot.with_lab
        def testcase_with_lab(lh: linux.Lab) -> None:
            lh.exec0("uname", "-a")

    This is essentially syntactic sugar for::

        import typing
        import tbot
        from tbot.machine import linux

        @tbot.testcase
        def testcase_with_lab(
            lab: typing.Optional[linux.Lab] = None,
        ) -> None:
            with lab or tbot.acquire_lab() as lh:
                lh.exec0("uname", "-a")

    .. warning::
        While making your life a lot easier, this decorator unfortunately has
        a drawback:  It will erase the type signature of your testcase, so you
        can no longer rely on type-checking when using the testcase downstream.
    """

    @functools.wraps(tc)
    def wrapped(
        lab: typing.Optional[linux.Lab] = None, *args: typing.Any, **kwargs: typing.Any
    ) -> typing.Any:
        if lab is not None and not isinstance(lab, linux.Lab):
            raise TypeError(f"Argument to {tc!r} must be a lab-host (found {lab!r})")
        with lab or selectable.acquire_lab() as lh:
            return tc(lh, *args, **kwargs)

    # Adjust annotation
    argname = tc.__code__.co_varnames[0]
    wrapped.__annotations__[argname] = typing.Optional[linux.Lab]

    return typing.cast(F_lab, wrapped)


F_ze = typing.TypeVar("F_ze", bound=typing.Callable[..., typing.Any])
F_zephyr = typing.Callable[
    [
        mypy.DefaultArg(typing.Union[selectable.LabHost, board.ZephyrShell, None]),
        mypy.VarArg(typing.Any),
        mypy.KwArg(typing.Any),
    ],
    typing.Any,
]


def with_zephyr(tc: F_ze) -> F_zephyr:
    """
    Decorate a function to automatically supply a Zephyr machine as an argument.

    The idea is that when using this decorator and calling the testcase
    without an already initialized Zephyr machine, tbot will automatically
    acquire the selected one.

    **Example**::

        from tbot.machine import board

        @tbot.testcase
        @tbot.with_zephyr
        def testcase_with_zephyr(ze: board.ZephyrShell) -> None:
            ze.exec0("version")

    This is essentially syntactic sugar for::

        import contextlib
        import typing
        import tbot
        from tbot.machine import board, linux

        @tbot.testcase
        def testcase_with_zephyr(
            lab_or_ze: typing.Union[linux.Lab, board.ZephyrShell, None] = None,
        ) -> None:
            with contextlib.ExitStack() as cx:
                lh: linux.Lab
                ze: board.ZephyrShell

                if isinstance(lab_or_ze, linux.Lab):
                    lh = cx.enter_context(lab_or_ze)
                elif isinstance(lab_or_ze, board.ZephyrShell):
                    lh = cx.enter_context(lab_or_ze.host)
                else:
                    lh = cx.enter_context(tbot.acquire_lab())

                if isinstance(lab_or_ze, board.ZephyrShell):
                    ze = cx.enter_context(lab_or_ze)
                else:
                    b = cx.enter_context(tbot.acquire_board(lh))
                    ze = cx.enter_context(tbot.acquire_zephyr(b))

                ze.exec("help")

    .. warning::
        While making your life a lot easier, this decorator unfortunately has
        a drawback:  It will erase the type signature of your testcase, so you
        can no longer rely on type-checking when using the testcase downstream.
    """

    @functools.wraps(tc)
    def wrapped(
        arg: typing.Union[selectable.LabHost, board.ZephyrShell, None] = None,
        *args: typing.Any,
        **kwargs: typing.Any,
    ) -> typing.Any:
        with contextlib.ExitStack() as cx:
            lh: selectable.LabHost
            ze: board.ZephyrShell

            # Acquire LabHost
            if arg is None:
                lh = cx.enter_context(selectable.acquire_lab())
            elif isinstance(arg, linux.Lab):
                lh = cx.enter_context(arg)
            elif not isinstance(arg, board.ZephyrShell):
                raise TypeError(
                    f"Argument to {tc!r} must either be a lab-host or a ZephyrShell (found {arg!r})"
                )

            # Acquire Zephyr
            if isinstance(arg, board.ZephyrShell):
                ze = cx.enter_context(arg)
            else:
                b = cx.enter_context(selectable.acquire_board(lh))
                ze = cx.enter_context(selectable.acquire_zephyr(b))

            return tc(ze, *args, **kwargs)

    # Adjust annotation
    argname = tc.__code__.co_varnames[0]
    wrapped.__annotations__[argname] = typing.Union[
        selectable.LabHost, board.ZephyrShell, None
    ]

    return typing.cast(F_zephyr, wrapped)


F_ub = typing.TypeVar("F_ub", bound=typing.Callable[..., typing.Any])
F_uboot = typing.Callable[
    [
        mypy.DefaultArg(typing.Union[selectable.LabHost, board.UBootShell, None]),
        mypy.VarArg(typing.Any),
        mypy.KwArg(typing.Any),
    ],
    typing.Any,
]


def with_uboot(tc: F_ub) -> F_uboot:
    """
    Decorate a function to automatically supply a U-Boot machine as an argument.

    The idea is that when using this decorator and calling the testcase
    without an already initialized U-Boot machine, tbot will automatically
    acquire the selected one.

    **Example**::

        from tbot.machine import board

        @tbot.testcase
        @tbot.with_uboot
        def testcase_with_uboot(ub: board.UBootShell) -> None:
            ub.exec0("version")

    This is essentially syntactic sugar for::

        import contextlib
        import typing
        import tbot
        from tbot.machine import board, linux

        @tbot.testcase
        def testcase_with_uboot(
            lab_or_ub: typing.Union[linux.Lab, board.UBootShell, None] = None,
        ) -> None:
            with contextlib.ExitStack() as cx:
                lh: linux.Lab
                ub: board.UBootShell

                if isinstance(lab_or_ub, linux.Lab):
                    lh = cx.enter_context(lab_or_ub)
                elif isinstance(lab_or_ub, board.UBootShell):
                    lh = cx.enter_context(lab_or_ub.host)
                else:
                    lh = cx.enter_context(tbot.acquire_lab())

                if isinstance(lab_or_ub, board.UBootShell):
                    ub = cx.enter_context(lab_or_ub)
                else:
                    b = cx.enter_context(tbot.acquire_board(lh))
                    ub = cx.enter_context(tbot.acquire_uboot(b))

                ub.exec0("version")

    .. warning::
        While making your life a lot easier, this decorator unfortunately has
        a drawback:  It will erase the type signature of your testcase, so you
        can no longer rely on type-checking when using the testcase downstream.
    """

    @functools.wraps(tc)
    def wrapped(
        arg: typing.Union[selectable.LabHost, board.UBootShell, None] = None,
        *args: typing.Any,
        **kwargs: typing.Any,
    ) -> typing.Any:
        with contextlib.ExitStack() as cx:
            lh: selectable.LabHost
            ub: board.UBootShell

            # Acquire LabHost
            if arg is None:
                lh = cx.enter_context(selectable.acquire_lab())
            elif isinstance(arg, linux.Lab):
                lh = cx.enter_context(arg)
            elif not isinstance(arg, board.UBootShell):
                raise TypeError(
                    f"Argument to {tc!r} must either be a lab-host or a UBootShell (found {arg!r})"
                )

            # Acquire U-Boot
            if isinstance(arg, board.UBootShell):
                ub = cx.enter_context(arg)
            else:
                b = cx.enter_context(selectable.acquire_board(lh))
                ub = cx.enter_context(selectable.acquire_uboot(b))

            return tc(ub, *args, **kwargs)

    # Adjust annotation
    argname = tc.__code__.co_varnames[0]
    wrapped.__annotations__[argname] = typing.Union[
        selectable.LabHost, board.UBootShell, None
    ]

    return typing.cast(F_uboot, wrapped)


F_lnx = typing.TypeVar("F_lnx", bound=typing.Callable[..., typing.Any])
F_linux = typing.Callable[
    [
        mypy.DefaultArg(typing.Union[selectable.LabHost, linux.LinuxShell, None]),
        mypy.VarArg(typing.Any),
        mypy.KwArg(typing.Any),
    ],
    typing.Any,
]


def with_linux(tc: F_lnx) -> F_linux:
    """
    Decorate a function to automatically supply a board Linux machine as an argument.

    The idea is that when using this decorator and calling the testcase
    without an already initialized Linux machine, tbot will automatically
    acquire the selected one.

    **Example**::

        from tbot.machine import linux

        @tbot.testcase
        @tbot.with_linux
        def testcase_with_linux(lnx: linux.LinuxShell) -> None:
            lnx.exec0("uname", "-a")

    .. warning::
        While making your life a lot easier, this decorator unfortunately has
        a drawback:  It will erase the type signature of your testcase, so you
        can no longer rely on type-checking when using the testcase downstream.
    """

    @functools.wraps(tc)
    def wrapped(
        arg: typing.Union[selectable.LabHost, linux.LinuxShell, None] = None,
        *args: typing.Any,
        **kwargs: typing.Any,
    ) -> typing.Any:
        with contextlib.ExitStack() as cx:
            lh: selectable.LabHost
            lnx: linux.LinuxShell

            # Acquire LabHost
            if arg is None:
                lh = cx.enter_context(selectable.acquire_lab())
            elif isinstance(arg, linux.Lab):
                lh = cx.enter_context(arg)  # type: ignore
            elif not isinstance(arg, linux.LinuxShell):
                raise TypeError(
                    f"Argument to {tc!r} must either be a lab-host or a board linux (found {arg!r})"
                )

            # Acquire Linux
            if arg is None or isinstance(arg, linux.Lab):
                b = cx.enter_context(selectable.acquire_board(lh))
                lnx = cx.enter_context(selectable.acquire_linux(b))
            else:
                lnx = cx.enter_context(arg)

            return tc(lnx, *args, **kwargs)

    # Adjust annotation
    argname = tc.__code__.co_varnames[0]
    wrapped.__annotations__[argname] = typing.Union[
        selectable.LabHost, linux.LinuxShell, None
    ]

    return typing.cast(F_linux, wrapped)
