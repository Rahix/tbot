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


class EnvScriptToolchain(Toolchain):
    """
    Toolchain that is initialized using an env script (e.g. yocto toolchain).

    **Example**:

    .. code-block:: python

        @property
        def toolchains(self):
            yocto_root = self.fsroot / "opt" / "poky" / "2.6"

            return {
                "cortexa8hf": linux.build.EnvScriptToolchain(
                    yocto_root / "environment-setup-cortexa8hf-neon-poky-linux-gnueabi",
                ),
            }
    """

    def __init__(self, path: "path.Path[Builder]") -> None:
        """
        Create a new EnvScriptToolchain.

        :param linux.Path path: Path to the env script
        """
        self.env_script = path

    def enable(self, host: "Builder") -> None:
        host.exec0("unset", "LD_LIBRARY_PATH")
        host.exec0("source", self.env_script)


class DistroToolchain(Toolchain):
    """
    Toolchain that was installed from distribution repositories.

    **Example**:

    .. code-block:: python

        @property
        def toolchains(self):
            return {
                "armv7a": linux.build.DistroToolchain("arm", "arm-linux-gnueabi-"),
                "armv8": linux.build.DistroToolchain("aarch64", "aarch64-linux-gnu-"),
            }
    """

    def __init__(self, arch: str, prefix: str) -> None:
        self.arch = arch
        self.prefix = prefix

    def enable(self, host: "Builder") -> None:
        host.env("ARCH", self.arch)
        host.env("CROSS_COMPILE", self.prefix)

        host.env("CC", self.prefix + "gcc")
        for tool in [
            "objdump",
            "size",
            "ar",
            "nm",
            "strings",
            "as",
            "ld",
            "objcopy",
            "readelf",
            "strip",
        ]:
            host.env(tool.upper(), self.prefix + tool)


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

        **Example**:

        .. code-block:: python

            @property
            def toolchains(self) -> typing.Dict[str, linux.build.Toolchain]:
                return {
                    "armv7a": linux.build.DistroToolchain("arm", "arm-linux-gnueabi-"),
                    "armv8": linux.build.DistroToolchain("aarch64", "aarch64-linux-gnu-"),
                    "mipsel": linux.build.DistroToolchain("mips", "mipsel-linux-gnu-"),
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

        assert isinstance(
            tc, Toolchain
        ), f"Toolchain {arch!r} is not an instance of `Toolchain` (is {tc!r})."

        with self.subshell():
            tc.enable(self)
            yield None
