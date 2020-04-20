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
import typing
import inspect


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

    def __init__(self, method: typing.Optional[str] = None) -> None:
        if method is None:
            # Grab the method name of the calling frame
            calling_frame = inspect.stack()[1]
            self.method = calling_frame.function
        else:
            self.method = method

        super().__init__(
            f"Called abstract method {self.method!r}.  This is probably an incorrect call to super()."
        )
