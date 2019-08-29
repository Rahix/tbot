import abc
import contextlib
import typing
import tbot
from .. import machine, shell, connector, channel


class PowerControl(machine.Initializer):
    @abc.abstractmethod
    def poweron(self) -> None:
        pass

    @abc.abstractmethod
    def poweroff(self) -> None:
        pass

    @contextlib.contextmanager
    def _init_machine(self) -> typing.Iterator:
        try:
            tbot.log.EventIO(
                ["board", "on", self.name],
                tbot.log.c("POWERON").bold + f" ({self.name})",
                verbosity=tbot.log.Verbosity.QUIET,
            )
            self.poweron()
            yield None
        finally:
            tbot.log.EventIO(
                ["board", "off", self.name],
                tbot.log.c("POWEROFF").bold + f" ({self.name})",
                verbosity=tbot.log.Verbosity.QUIET,
            )
            self.poweroff()


class Board(shell.RawShell):
    pass


class Connector(connector.Connector):
    def __init__(self, board: Board) -> None:
        if not isinstance(board, Board):
            raise TypeError(
                f"{self.__class__!r} can only be instanciated from a `Board` (got {board!r})."
            )
        self._board = board
        self.host = getattr(board, "host", None)

    @contextlib.contextmanager
    def _connect(self) -> typing.Iterator[channel.Channel]:
        with self._board.ch.borrow() as ch:
            yield ch

    def clone(self) -> typing.NoReturn:
        raise NotImplementedError("abstract method")
