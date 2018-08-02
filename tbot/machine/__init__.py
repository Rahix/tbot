import abc


class Machine(abc.ABC):
    """Connect to a machine (host, board, etc.)."""

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Return the name of this machine."""
        pass
