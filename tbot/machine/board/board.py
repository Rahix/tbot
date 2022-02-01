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
import time
import typing

import tbot
import tbot.error

from .. import channel, connector, machine, shell


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

    powercycle_delay: float = 0
    """
    Delay between a poweroff and a subsequent poweron.

    This delay is only accounted for when both poweroff and poweron happen in
    the same tbot process.  If you are calling tbot multiple times really fast,
    the delay is not performed!

    Using this attribute over, for example, a ``time.sleep()`` call in the
    ``poweroff()`` implementation has the advantage that the delay is not
    performed at the end of a tbot run, only for powercycles "in the middle".

    .. versionadded:: 0.9.3
    """

    @contextlib.contextmanager
    def _init_machine(self) -> typing.Iterator:
        if not self.power_check():
            raise Exception("Board is already on, someone else might be using it!")

        # If the board was previously powered off, ensure that at least
        # `self.powercycle_delay` passes before powering on again.
        if (
            hasattr(self.__class__, "_last_poweroff_timestamp")
            and self.powercycle_delay > 0
        ):
            passed_time = time.monotonic() - getattr(
                self.__class__, "_last_poweroff_timestamp"
            )
            delay_time = self.powercycle_delay - passed_time
            if delay_time > 0:
                time.sleep(delay_time)

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

            # Set the timestamp of last poweroff so we can reference it during
            # next poweron to optionally delay for a short while.
            setattr(self.__class__, "_last_poweroff_timestamp", time.monotonic())


class Board(shell.RawShell):
    """
    Base class for board-machines.

    This class does nothing special except providing the ``.interactive()``
    method for directly interacting with the serial-console.
    """

    pass


class BoardMachineBase(abc.ABC):
    """
    ABC/Protocol Class for any kind of board machines.
    """

    @property
    @abc.abstractmethod
    def board(self) -> Board:
        """
        Returns the instance of the underlying board machine on which this
        machine is "running".
        """
        raise tbot.error.AbstractMethodError()


M = typing.TypeVar("M", bound=machine.Machine)


class Connector(connector.Connector, BoardMachineBase):
    def __init__(self, board: typing.Union[Board, channel.Channel]) -> None:
        if not (isinstance(board, Board) or isinstance(board, channel.Channel)):
            raise TypeError(
                f"{self.__class__!r} can only be instantiated from a `Board` (got {board!r})."
            )
        self._board = board
        self.host = getattr(board, "host", None)

    @classmethod
    @contextlib.contextmanager
    def from_context(cls: typing.Type[M], ctx: "tbot.Context") -> typing.Iterator[M]:
        with contextlib.ExitStack() as cx:
            b = cx.enter_context(ctx.request(tbot.role.Board, exclusive=True))
            m = cx.enter_context(cls(b))  # type: ignore
            yield m

    @contextlib.contextmanager
    def _connect(self) -> typing.Iterator[channel.Channel]:
        if isinstance(self._board, channel.Channel):
            yield self._board
        else:
            with self._board.ch.borrow() as ch:
                yield ch

    def clone(self) -> typing.NoReturn:
        raise tbot.error.AbstractMethodError()

    @property
    def board(self) -> Board:
        if not isinstance(self._board, Board):
            raise Exception("this machine was not instantiated from a `Board`!")
        return self._board
