import abc
import typing
from tbot import machine
from tbot.machine import channel
from . import board

B = typing.TypeVar("B", bound=board.Board)


class BoardMachine(machine.Machine, typing.Generic[B]):
    @abc.abstractmethod
    def connect(self) -> channel.Channel:
        pass

    def __init__(self, board: B) -> None:
        self.board = board
        self.channel = self.connect()

    def destroy(self) -> None:
        self.channel.close()
