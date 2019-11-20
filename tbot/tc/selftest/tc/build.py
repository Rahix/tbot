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

import typing
import tbot
from tbot.machine import linux, connector

__all__ = ("selftest_tc_build_toolchain",)


class LocalDummyBuildhost(connector.SubprocessConnector, linux.Bash, linux.Builder):
    name = "dummy-build"

    @property
    def toolchains(self) -> typing.Dict[str, linux.build.Toolchain]:
        """Return toolchains available on this host."""
        return {
            "selftest-toolchain": linux.build.EnvScriptToolchain(
                self.workdir / ".selftest-toolchain.sh"
            )
        }

    @staticmethod
    def prepare(h: linux.LinuxShell) -> None:
        h.exec0(
            "echo",
            "export CC=dummy-none-gcc",
            linux.RedirStdout(h.workdir / ".selftest-toolchain.sh"),
        )


@tbot.testcase
def selftest_tc_build_toolchain(lab: typing.Optional[linux.Lab] = None,) -> None:
    """Test connecting to a buildhost and enabling a toolchain on there."""
    with LocalDummyBuildhost() as bh:
        tbot.log.message("Creating dummy toolchain ...")
        bh.prepare(bh)

        tbot.log.message("Attempt using it ...")
        cc = bh.env("CC")
        assert cc != "dummy-none-gcc", repr(cc)

        with bh.enable("selftest-toolchain"):
            cc = bh.env("CC")
            assert cc == "dummy-none-gcc", repr(cc)

        cc = bh.env("CC")
        assert cc != "dummy-none-gcc", repr(cc)
