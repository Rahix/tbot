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

import abc
import contextlib
import typing
import tbot
from .. import linux, machine, shell, connector, channel


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

    def power_check(self) -> bool:
        """
        Check if the board is already on and someone else might be using it.

        Implementations of this function should raise an exception in case they
        detect the board to be on or return ``False``.  If the board is off and
        ready to be used, an implementation should return ``True``.
        """
        return True

    @contextlib.contextmanager
    def _init_machine(self) -> typing.Iterator:
        if not self.power_check():
            raise Exception("Board is already on, someone else might be using it!")

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
    def add_blobs(self, path: linux.Path) -> None:
        """
        Copy binary blobs needed to build to the given parth

        :param linux.Path path: Path to the build directory.
        """
        pass

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
