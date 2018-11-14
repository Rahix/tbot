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
from . import toolchain


class BuildMachine(linux.LinuxMachine):
    """Generic buildhost machine."""

    @property
    @abc.abstractmethod
    def toolchains(self) -> typing.Dict[str, toolchain.Toolchain]:
        """
        Return a dictionary of all toolchains that exist on this buildhost.

        **Example**::

            @property
            def toolchains(self) -> typing.Dict[str, linux.build.Toolchain]:
                return {
                    "generic-armv7a": linux.build.EnvScriptToolchain(
                        linux.Path(
                            self,
                            "/path/to/environment-setup-armv7a-neon-poky-linux-gnueabi",
                        )
                    ),
                    "generic-armv7a-hf": linux.build.EnvScriptToolchain(
                        linux.Path(
                            self,
                            "/path/to/environment-setup-armv7ahf-neon-poky-linux-gnueabi",
                        )
                    ),
                }
        """
        pass

    def enable(self, arch: str) -> "_ToolchainContext":
        """
        Enable the toolchain for ``arch`` on this BuildHost instance.

        **Example**::

            with lh.build() as bh:
                # Now we are on the buildhost

                with bh.enable("generic-armv7a-hf"):
                    # Toolchain is enabled here
                    bh.exec0(linux.Env("CC"), "--version")
        """
        tc = self.toolchains[arch]

        return _ToolchainContext(self, tc)


class _ToolchainContext(linux._SubshellContext):
    __slots__ = ("h", "tc")

    def __init__(self, h: BuildMachine, tc: toolchain.Toolchain) -> None:
        super().__init__(h)
        self.h = h
        self.tc = tc

    def __enter__(self) -> None:
        super().__enter__()
        self.tc.enable(self.h)
