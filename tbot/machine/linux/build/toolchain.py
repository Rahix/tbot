import abc
import typing
from tbot.machine import linux


class Toolchain(abc.ABC):
    @abc.abstractmethod
    def enable(self, host: linux.LinuxMachine) -> None:
        pass


H = typing.TypeVar("H", bound=linux.LinuxMachine)


class EnvScriptToolchain(Toolchain):
    def enable(self, host: H) -> None:
        host.exec0("unset", "LD_LIBRARY_PATH")
        host.exec0("source", self.env_script)

    def __init__(self, path: linux.Path[H]) -> None:
        self.env_script = path
