import abc
import contextlib
import time
import typing
import tbot
from tbot.machine import linux
from tbot.machine import channel

Self = typing.TypeVar("Self", bound="Board")


class Board(contextlib.AbstractContextManager):
    """
    Abstract base class for boards.

    **Implementation example**::

        from tbot.machine import board
        from tbot.machine import channel
        from tbot.machine import linux

        class MyBoard(board.Board):
            name = "my-board"

            def poweron(self) -> None:
                # Command to power on the board
                self.lh.exec0("poweron", self.name)

            def poweroff(self) -> None:
                # Command to power off the board
                self.lh.exec0("poweroff", self.name)

            def connect(self) -> channel.Channel:
                return self.lh.new_channel(
                    "picocom",
                    "-b",
                    "115200",
                    linux.Path(self.lh, "/dev") / f"tty-{self.name}",
                )
    """

    @property
    def connect_wait(self) -> typing.Optional[float]:
        """
        Time to wait after connecting before powering on (:class:`float`).

        This is supposed to allow telnet/rlogin/whatever to take some time
        to establish the connection.
        """
        pass

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Name of this board."""
        pass

    @abc.abstractmethod
    def poweron(self) -> None:
        """Power on this board."""
        pass

    @abc.abstractmethod
    def poweroff(self) -> None:
        """Power off this board."""
        pass

    def connect(self) -> typing.Optional[channel.Channel]:
        """Connect to the serial port of this board."""
        return None

    def __init__(self, lh: linux.LabHost) -> None:
        """
        Initialize an instance of this board.

        This will not yet power on the board. For that you need to use a ``with``
        block::

            with MyBoard(lh) as b:
                ...

        :param tbot.machine.linux.LabHost lh: LabHost from where to connect to the Board.
        """
        self.lh = lh
        self.boot_ev = tbot.log.EventIO(verbosity=tbot.log.Verbosity.QUIET)
        self.channel = self.connect()
        if self.connect_wait is not None:
            time.sleep(self.connect_wait)
        if self.channel is not None and not self.channel.isopen():
            raise RuntimeError("Could not connect to board!")
        self._rc = 0

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.lh!r})"

    def __enter__(self: Self) -> Self:
        self._rc += 1
        if self._rc > 1:
            return self
        self.boot_ev.writeln(tbot.log.c("POWERON").bold + f" ({self.name})")
        self.boot_ev.verbosity = tbot.log.Verbosity.STDOUT
        self.boot_ev.prefix = "   <> "
        self.poweron()
        self.on = True
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:  # type: ignore
        self._rc -= 1
        if self._rc == 0:
            tbot.log.EventIO(
                tbot.log.c("POWEROFF").bold + f" ({self.name})",
                verbosity=tbot.log.Verbosity.QUIET,
            )
            self.poweroff()
