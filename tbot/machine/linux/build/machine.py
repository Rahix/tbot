import abc
import typing
from tbot.machine import linux
from . import toolchain


class BuildMachine(linux.LinuxMachine):
    @property
    @abc.abstractmethod
    def toolchains(self) -> typing.Dict[str, toolchain.Toolchain]:
        pass

    def enable(self, arch: str) -> None:
        tc = self.toolchains[arch]

        tc.enable(self)

    def __init__(self, arch: typing.Optional[str] = None, *args: typing.Any, **kwargs: typing.Any) -> None:
        super().__init__(*args, **kwargs)  # type: ignore

        if arch is not None:
            self.enable(arch)
