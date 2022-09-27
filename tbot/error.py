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
import inspect
import typing
from typing import Any, Optional

if typing.TYPE_CHECKING:
    from tbot import machine


class TbotException(Exception):
    """
    Base-class for all exceptions which are specific to tbot.
    """

    pass


class AbstractMethodError(TbotException, NotImplementedError):
    """
    A method which needs to be overwritten was called from code.  This
    shouldn't ever really happen in practice hopefully ...
    """

    def __init__(self, method: Optional[str] = None) -> None:
        if method is None:
            # Grab the method name of the calling frame
            calling_frame = inspect.stack()[1]
            self.method = calling_frame.function
        else:
            self.method = method

        super().__init__(
            f"Called abstract method {self.method!r}.  This is probably an incorrect call to super()."
        )


class WrongHostError(TbotException, ValueError):
    """
    A method was called with arguments that reference a different host.
    """

    def __init__(self, arg: Any, host: "machine.Machine") -> None:
        self.arg = arg
        self.host = host

        super().__init__(f"{arg!r} references a host/machine that is not {host!r}")


class ContextError(TbotException, RuntimeError):
    """
    A forbidden or wrong kind of interaction with tbot's context was attempted.

    The exception message will include more details.  As an example, this
    exception is raised when requesting an instance that is currently
    exclusively requested elsewhere.

    .. versionadded:: UNRELEASED
    """
