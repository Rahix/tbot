import abc
import contextlib
import typing
import tbot
from .. import machine, shell, connector, channel


class PowerControl(machine.Initializer):
    """
    Machine-initializer for controlling power for a hardware.

    When initializing, :py:meth:`~tbot.machine.board.PowerControl.poweron` is
    called and when deinitializing,
    :py:meth:`~tbot.machine.board.PowerControl.poweroff` is called.
    """

    @abc.abstractmethod
    def poweron(self) -> None:
        """
        Power-on the hardware.

        If the machine is using the
        :py:class:`~tbot.machine.connector.ConsoleConnector`, you can use
        ``self.host.exec0()`` to run commands on the lab-host.

        **Example**:

        .. code-block::

            def poweron(self):
                self.host.exec0("power-control.sh", "on")
        """
        pass

    @abc.abstractmethod
    def poweroff(self) -> None:
        """
        Power-off the hardware.
        """
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
    """
    Base class for board-machines.

    This class does nothing special except providing the ``.interactive()``
    method for directly interacting with the serial-console.
    """

    pass


class Connector(connector.Connector):
    def __init__(self, board: typing.Union[Board, channel.Channel]) -> None:
        if not (isinstance(board, Board) or isinstance(board, channel.Channel)):
            raise TypeError(
                f"{self.__class__!r} can only be instanciated from a `Board` (got {board!r})."
            )
        self._board = board
        self.host = getattr(board, "host", None)

    @contextlib.contextmanager
    def _connect(self) -> typing.Iterator[channel.Channel]:
        if isinstance(self._board, channel.Channel):
            yield self._board
        else:
            with self._board.ch.borrow() as ch:
                yield ch

    def clone(self) -> typing.NoReturn:
        raise NotImplementedError("abstract method")
