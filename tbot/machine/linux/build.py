# tbot, Embedded Automation Tool
# Copyright (C) 2019  Harald Seiler
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
import contextlib
import typing

from . import linux_shell, path


class Toolchain(abc.ABC):
    """Generic toolchain type."""

    @abc.abstractmethod
    def enable(self, host: "Builder") -> None:
        """Enable this toolchain on the given ``host``."""
        pass


H = typing.TypeVar("H", bound="Builder")


class EnvScriptToolchain(Toolchain):
    """Toolchain that is initialized using an env script."""

    def enable(self, host: H) -> None:
        host.exec0("unset", "LD_LIBRARY_PATH")
        host.exec0("source", self.env_script)

    def __init__(self, path: path.Path[H]) -> None:
        """
        Create a new EnvScriptToolchain.

        :param linux.Path path: Path to the env script
        """
        self.env_script = path


class Builder(linux_shell.LinuxShell):
    """
    Mixin to mark a machine as a build-host.

    You need to define the ``toolchain()`` method when using this mixin.  You
    can then use the ``enable()`` method to enable a toolchain and compile
    projects with it:

    .. code-block:: python

        with MyBuildHost(lh) as bh:
            bh.exec0("uptime")

            with bh.enable("generic-armv7a-hf"):
                cc = bh.env("CC")
                bh.exec0(linux.Raw(cc), "main.c")

    .. note::

        If you look closely, I have used ``linux.Raw(cc)`` in the ``exec0()``
        call.  This is necessary because a lot of toolchains define ``$CC`` as
        something like

        .. code-block:: text

            CC=arm-poky-linux-gnueabi-gcc -march=armv7-a -mfpu=neon -mfloat-abi=hard -mcpu=cortex-a8

        where some parameters are already included.  Without the
        :py:class:`linux.Raw <tbot.machine.linux.Raw>`, tbot would run

        .. code-block:: shell-session

            $ "${CC}" main.c

        where the arguments are interpreted as part of the path to the compiler.
        This will obviously fail so instead, with the :py:class:`linux.Raw
        <tbot.machine.linux.Raw>`,
        tbot will run

        .. code-block:: shell-session

            $ ${CC} main.c

        where the shell expansion will do the right thing.
    """

    @property
    @abc.abstractmethod
    def toolchains(self) -> typing.Dict[str, Toolchain]:
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

    @contextlib.contextmanager
    def enable(self, arch: str) -> typing.Iterator[None]:
        """
        Enable the toolchain for ``arch`` on this BuildHost instance.

        **Example**::

            with lh.build() as bh:
                # Now we are on the buildhost

                with bh.enable("generic-armv7a-hf"):
                    # Toolchain is enabled here
                    cc = bh.env("CC")
                    bh.exec0(linux.Raw(cc), "--version")
        """
        tc = self.toolchains[arch]

        with self.subshell():
            tc.enable(tc, self)
            yield None
