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
