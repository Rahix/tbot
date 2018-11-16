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

Self = typing.TypeVar("Self", bound="Machine")


class Machine(typing.ContextManager):
    """Connect to a machine (host, board, etc.)."""

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Name of this machine."""
        pass

    @abc.abstractmethod
    def destroy(self) -> None:
        """Destroy and cleanup this machine."""
        pass

    def __init__(self) -> None:
        """Connect to this machine."""
        self._rc = 0

    def __enter__(self: Self) -> Self:
        self._rc += 1
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:  # type: ignore
        """Cleanup this machine instance."""
        self._rc -= 1
        if self._rc == 0:
            self.destroy()


class InteractiveMachine(abc.ABC):
    """Machine that can be used interactively."""

    @abc.abstractmethod
    def interactive(self) -> None:
        """
        Drop into an interactive shell on this machine.

        :raises RuntimeError: If TBot was not able to reacquire the shell
            after the session finished.
        """
        pass
