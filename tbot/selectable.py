import typing
from tbot.machine import linux
from tbot.machine.linux import lab
from tbot.machine import board


class LabHost(lab.LocalLabHost, typing.ContextManager):
    """
    Default LabHost type.

    Might be replaced by another LabHost if one was selected on
    the commandline using ``-l <lab.py>``
    """

    def __enter__(self) -> "LabHost":
        return typing.cast(LabHost, super().__enter__())

    @property
    def workdir(self) -> "linux.Path[LabHost]":  # noqa: D102
        wd = super().workdir
        return linux.Path(self, wd)


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


class Board(board.Board):
    """Dummy type that will be replaced by the actual selected board at runtime."""

    _unselected = True

    name = "dummy"

    def __init__(self, lh: linux.LabHost) -> None:  # noqa: D107
        raise NotImplementedError("This is a dummy Board")

    def poweron(self) -> None:  # noqa: D102
        raise NotImplementedError("This is a dummy Board")

    def poweroff(self) -> None:  # noqa: D102
        raise NotImplementedError("This is a dummy Board")


def acquire_board(lh: LabHost) -> Board:
    """
    Acquire a handle to the selected board.

    The returned board must be used in a with statement to be powered on.

    :rtype: tbot.machine.board.Board
    """
    if hasattr(Board, "_unselected"):
        raise NotImplementedError("Maybe you haven't set a board?")
    return Board(lh)


class UBootMachine(board.UBootMachine[Board]):
    """Dummy type that will be replaced by the actual selected U-Boot machine at runtime."""

    _unselected = True

    def __init__(self, b: typing.Any) -> None:  # noqa: D107
        raise NotImplementedError("This is a dummy Linux")


def acquire_uboot(board: Board) -> UBootMachine:
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
    return UBootMachine(board)


class LinuxMachine(board.LinuxMachine[Board], typing.ContextManager):
    """Dummy type that will be replaced by the actual selected Linux machine at runtime."""

    _unselected = True

    def __init__(self, b: typing.Any) -> None:  # noqa: D107
        raise NotImplementedError("This is a dummy Linux")

    password = None
    shell = linux.shell.Shell


def acquire_linux(b: typing.Union[Board, UBootMachine]) -> LinuxMachine:
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
    return LinuxMachine(b)
