import typing
from tbot.machine import linux
from tbot.machine.linux import lab
from tbot.machine import board


class LabHost(lab.LocalLabHost, typing.ContextManager):
    pass


def acquire_lab() -> LabHost:
    if hasattr(LabHost, "_unselected"):
        raise NotImplementedError("Maybe you haven't set a lab?")
    return LabHost()


class Board(board.Board):
    """
    Dummy type that will be replaced by the actual board at runtime.
    """
    _unselected = True

    name = "dummy"

    def __init__(self, lh: linux.LabHost) -> None:
        raise NotImplementedError("This is a dummy Board")

    def poweron(self) -> None:
        raise NotImplementedError("This is a dummy Board")

    def poweroff(self) -> None:
        raise NotImplementedError("This is a dummy Board")


def acquire_board(lh: LabHost) -> Board:
    if hasattr(Board, "_unselected"):
        raise NotImplementedError("Maybe you haven't set a board?")
    return Board(lh)


class UBootMachine(board.UBootMachine[Board]):
    """
    Dummy type that will be replaced by the actual U-Boot machine at runtime.
    """
    _unselected = True

    def __init__(self, b: typing.Any) -> None:
        raise NotImplementedError("This is a dummy Linux")


def acquire_uboot(board: Board) -> UBootMachine:
    if hasattr(UBootMachine, "_unselected"):
        raise NotImplementedError("Maybe you haven't set a board?")
    return UBootMachine(board)


class LinuxMachine(board.LinuxMachine[Board], typing.ContextManager):
    """
    Dummy type that will be replaced by the actual Linux machine at runtime.
    """
    _unselected = True

    def __init__(self, b: typing.Any) -> None:
        raise NotImplementedError("This is a dummy Linux")

    password = None


def acquire_linux(b: typing.Union[Board, UBootMachine]) -> LinuxMachine:
    if hasattr(LinuxMachine, "_unselected"):
        raise NotImplementedError("Maybe you haven't set a board?")
    return LinuxMachine(b)
