# tbot, Embedded Automation Tool
# Copyright (C) 2020  Harald Seiler
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

import tbot
from tbot.machine import board


@tbot.named_testcase("uboot_smoke_test")
@tbot.with_uboot
def smoke_test(ub: board.UBootShell) -> None:
    ub.exec0("version")
    ub.exec0("bdinfo")
    ub.exec0("printenv")
