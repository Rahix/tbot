import abc
import typing
from tbot.machine import linux


class Toolchain(abc.ABC):
    """Generic toolchain type."""

    @abc.abstractmethod
    def enable(self, host: linux.LinuxMachine) -> None:
        """Enable this toolchain on the given ``host``."""
        pass


H = typing.TypeVar("H", bound=linux.LinuxMachine)


class EnvScriptToolchain(Toolchain):
    """Toolchain that is initialized using an env script."""

    def enable(self, host: H) -> None:  # noqa: D102
        host.exec0("unset", "LD_LIBRARY_PATH")
        host.exec0("source", self.env_script)

    def __init__(self, path: linux.Path[H]) -> None:
        """
        Create a new EnvScriptToolchain.

        :param linux.Path path: Path to the env script
        """
        self.env_script = path
