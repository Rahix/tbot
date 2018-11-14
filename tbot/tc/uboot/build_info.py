import abc
import typing
from tbot.machine import linux
from tbot.tc import git

BH = typing.TypeVar("BH", bound=linux.LinuxMachine)


class BuildInfo(abc.ABC, typing.Generic[BH]):
    uboot_remote = "git://git.denx.de/u-boot.git"

    @property
    @abc.abstractmethod
    def name(self) -> str:
        pass

    def checkout(self, clean: bool = True) -> git.GitRepository[BH]:
        return git.GitRepository(
            target=self.h.workdir / f"uboot-{self.name}",
            url=self.uboot_remote,
            clean=clean,
            rev="master",
        )

    @property
    @abc.abstractmethod
    def defconfig(self) -> str:
        pass

    @property
    def toolchain(self) -> typing.Optional[str]:
        return None

    def __init__(self, h: BH) -> None:
        self.h = h
