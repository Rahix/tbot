import abc
import contextlib
import time
import typing
import tbot
from tbot.machine import linux
from tbot.machine import channel

Self = typing.TypeVar("Self", bound="Board")


class Board(contextlib.AbstractContextManager):
    connect_wait: typing.Optional[float] = None

    @property
    @abc.abstractmethod
    def name(self) -> str:
        pass

    @abc.abstractmethod
    def poweron(self) -> None:
        pass

    @abc.abstractmethod
    def poweroff(self) -> None:
        pass

    def connect(self) -> typing.Optional[channel.Channel]:
        return None

    def __init__(self, lh: linux.LabHost) -> None:
        self.lh = lh
        self.boot_ev = tbot.log.EventIO()
        self.channel = self.connect()
        if self.connect_wait is not None:
            time.sleep(self.connect_wait)
        self.on = False

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.lh!r})"

    def __enter__(self: Self) -> Self:
        if self.on:
            raise RuntimeError("Board already powered on!")
        self.boot_ev.writeln(tbot.log.c("POWERON").bold + f" ({self.name})")
        self.boot_ev.prefix = "   <> "
        self.poweron()
        self.on = True
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:  # type: ignore
        """Cleanup this machine instance."""
        tbot.log.EventIO(tbot.log.c("POWEROFF").bold + f" ({self.name})")
        self.poweroff()
