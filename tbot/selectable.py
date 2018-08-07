from tbot.machine.linux import lab
from tbot.machine import board


class LabHost(lab.LabHost):
    """
    Dummy type that will be replaced by the actual lab at runtime.
    """
    _unselected = True


def acquire_lab() -> LabHost:
    if hasattr(LabHost, "_unselected"):
        raise NotImplementedError("Maybe you haven't set a lab?")
    return LabHost()  # type: ignore


class Board(board.Board):
    """
    Dummy type that will be replaced by the actual board at runtime.
    """
    _unselected = True


def acquire_board(lh: LabHost) -> Board:
    if hasattr(Board, "_unselected"):
        raise NotImplementedError("Maybe you haven't set a board?")
    return Board(lh)  # type: ignore


class UBootMachine(board.UBootMachine):
    """
    Dummy type that will be replaced by the actual U-Boot machine at runtime.
    """
    _unselected = True


def acquire_uboot(board: Board) -> UBootMachine:
    if hasattr(UBootMachine, "_unselected"):
        raise NotImplementedError("Maybe you haven't set a board?")
    return UBootMachine(board)  # type: ignore
