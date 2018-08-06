import abc
import contextlib
from tbot.machine.linux import lab


class Board(contextlib.AbstractContextManager):
    @abc.abstractmethod
    def poweron(self) -> None:
        pass

    @abc.abstractmethod
    def poweroff(self) -> None:
        pass

    def __init__(self, lh: lab.LabHost) -> None:
        self.lh = lh

    def __enter__(self) -> "Board":
        self.poweron()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:  # type: ignore
        """Cleanup this machine instance."""
        self.poweroff()
