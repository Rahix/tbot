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

import re
from .. import channel


def wait_for_shell(ch: channel.Channel) -> None:
    # Repeatedly sends `echo TBOT''LOGIN\r`.  At some point, the shell
    # interprets this command and prints out `TBOTLOGIN` because of the
    # quotation-marks being removed.  Once we detect this, this function
    # can return, knowing the shell is now running on the other end.
    #
    # Credit to Pavel for this idea!
    with ch.with_prompt(re.compile(b"TBOTLOGIN.{0,80}", re.DOTALL)):
        while True:
            ch.sendline("echo TBOT''LOGIN")
            try:
                ch.read_until_prompt(timeout=0.2)
                break
            except TimeoutError:
                pass
