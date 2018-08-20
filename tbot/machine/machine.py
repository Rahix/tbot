import abc
import contextlib
import typing

Self = typing.TypeVar("Self", bound="Machine")


class Machine(contextlib.AbstractContextManager):
    """Connect to a machine (host, board, etc.)."""

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Return the name of this machine."""
        pass

    @abc.abstractmethod
    def destroy(self) -> None:
        """Destroy and cleanup this machine instance."""
        pass

    def __init__(self) -> None:
        self._rc = 0

    def __enter__(self: Self) -> Self:
        self._rc += 1
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:  # type: ignore
        """Cleanup this machine instance."""
        self._rc -= 1
        if self._rc == 0:
            self.destroy()


class InteractiveMachine(abc.ABC):
    @abc.abstractmethod
    def interactive(self) -> None:
        pass
