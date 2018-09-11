import typing
from tbot import machine
from . import board

B = typing.TypeVar("B", bound=board.Board)


class BoardMachine(machine.Machine, typing.Generic[B]):

    def __init__(self, board: B) -> None:
        super().__init__()
        self.board: B = board

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.board!r})"
