# TBot, Embedded Automation Tool
# Copyright (C) 2018  Harald Seiler
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import abc
import typing
from tbot.machine import linux
from tbot.tc import git

BH = typing.TypeVar("BH", bound=linux.LinuxMachine)


class BuildInfo(abc.ABC, typing.Generic[BH]):
    """
    Info for building U-Boot.

    Inherit this class in your board config to configure building
    U-Boot.
    """

    uboot_remote = "git://git.denx.de/u-boot.git"

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """
        Name of this build.

        Should be unique for each unique U-Boot config.
        """
        pass

    def checkout(self, clean: bool = True) -> git.GitRepository[BH]:
        """
        Checkout U-Boot for this config.

        Defaults to checking out ``self.uboot_remote`` (=``git://git.denx.de/u-boot.git``).

        Overwrite this method to specify a custom checkout procedure (eg.
        patching the repo afterwards)
        """

        return git.GitRepository(
            target=self.h.workdir / f"uboot-{self.name}",
            url=self.uboot_remote,
            clean=clean,
            rev="master",
        )

    @property
    @abc.abstractmethod
    def defconfig(self) -> str:
        """Defconfig to use for U-Boot."""
        pass

    @property
    def toolchain(self) -> typing.Optional[str]:
        """
        Toolchain for building U-Boot.

        Must be defined for the selected :class:`~tbot.machine.linux.BuildMachine`.
        """
        return None

    def __init__(self, h: BH) -> None:  # noqa: D107
        self.h = h
