import abc
import contextlib


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

    def __exit__(self, exc_type, exc_value, traceback) -> None:  # type: ignore
        """Cleanup this machine instance."""
        self.destroy()
