# tbot, Embedded Automation Tool
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

import contextlib
import typing
import tbot
from tbot.machine import linux
from tbot.tc import uboot

BH = typing.TypeVar("BH", bound=linux.BuildMachine)


@tbot.testcase
def build(
    build_machine: typing.Optional[BH] = None,
    build_info: typing.Optional[typing.Type[uboot.BuildInfo]] = None,
    clean: bool = True,
) -> linux.Path[BH]:
    """
    Build U-Boot.

    .. deprecated:: 0.6.6
        This testcase has serious design flaws.  You can still use it until
        the new version is implemented, but be aware that it will change at
        some point.

    :param linux.BuildMachine build_machine: Machine where to build U-Boot
    :param uboot.BuildInfo build_info: Build parameters, defaults to the info
        associated with the selected board.  This info is defined like this::

            class MyBoardUBootBuild(uboot.BuildInfo):
                name = "myboard"
                defconfig = "myboard_defconfig"
                toolchain = "generic-armv7a-hf"

            class MyBoardUBoot(board.UBootMachine[MyBoard]):
                prompt = "=> "
                build = MyBoardUBootBuild
    :rtype: linux.Path
    :returns: Path to the build dir
    """
    with contextlib.ExitStack() as cx:
        if build_machine is not None:
            bh: linux.BuildMachine = build_machine
        else:
            lh = cx.enter_context(tbot.acquire_lab())
            bh = cx.enter_context(lh.build())

        if build_info is not None:
            bi = build_info(bh)
        else:
            bi = getattr(tbot.selectable.UBootMachine, "build")(bh)

        repo = bi.checkout(clean)

        with bh if bi.toolchain is None else bh.enable(bi.toolchain):
            bh.exec0("cd", repo)
            if clean:
                bh.exec0("make", "mrproper")
                bh.exec0("make", bi.defconfig)

            nproc = bh.exec0("nproc", "--all").strip()
            bh.exec0("make", "-j", nproc, "all")

        return repo
