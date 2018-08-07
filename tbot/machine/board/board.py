import abc
import contextlib
import typing
import tbot
from tbot.machine.linux import lab

Self = typing.TypeVar("Self", bound="Board")


class Board(contextlib.AbstractContextManager):
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

    def __init__(self, lh: lab.LabHost) -> None:
        self.lh = lh
        self.ev = tbot.log.EventIO()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.lh!r})"

    def __enter__(self: Self) -> Self:
        self.ev.writeln(tbot.log.c("POWERON").bold + f" ({self.name})")
        self.ev.prefix = "   <> "
        self.poweron()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:  # type: ignore
        """Cleanup this machine instance."""
        tbot.log.EventIO(tbot.log.c("POWEROFF").bold + f" ({self.name})")
        self.poweroff()
