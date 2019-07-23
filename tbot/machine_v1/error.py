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

import typing
from tbot import machine


class CommandFailedException(Exception):
    """Command that was issued did not finish successfully."""

    def __init__(
        self,
        host: machine.Machine,
        command: str,
        stdout: typing.Optional[str],
        *args: typing.Any,
    ) -> None:
        """
        Create a new CommandFailedException.

        :param machine.Machine host: The machine the command was issued on
        :param str command: The command that failed
        :param str stdout: Optional output of the command
        """
        super().__init__(*args)
        self.host = host
        self.command = command
        self.stdout = stdout

    def __str__(self) -> str:
        return f"[{self.command}] failed!"


class WrongHostException(Exception):
    """The host associated with an object did not match."""

    def __init__(self, host: machine.Machine, arg: typing.Any) -> None:
        """
        Create a new WrongHostException.

        :param machine.Machine host: The wrong host
        :param arg: The object that is not associated with host
        """
        super().__init__()
        self.host = host
        self.arg = arg

    def __str__(self) -> str:
        return f"{self.arg!r} is not associated with {self.host!r}"
