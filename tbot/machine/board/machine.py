import typing
from tbot import machine
from . import board

B = typing.TypeVar("B", bound=board.Board)


class BoardMachine(machine.Machine, typing.Generic[B]):
    """Abstract base for board machines."""

    def __init__(self, board: B) -> None:
        """
        Create a new board machine.

        :param tbot.machine.board.Board board: The board this machine should use.
        """
        super().__init__()
        self.board: B = board

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.board!r})"
