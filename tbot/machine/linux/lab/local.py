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

import typing
import getpass
from tbot.machine import linux
from tbot.machine import channel
from .machine import LabHost

LLH = typing.TypeVar("LLH", bound="LocalLabHost")


class LocalLabHost(LabHost):
    """
    LabHost on the host TBot is running on.

    Makes use of the :class:`~tbot.machine.channel.SubprocessChannel`.

    ``LocalLabHost`` can be instanciated as is, but if you need customization,
    you should subclass it.
    """

    name = "local"

    @property
    def workdir(self: LLH) -> "linux.Path[LLH]":
        """
        Return a path to a workdir for TBot.

        Defaults to ``/tmp/tbot-wd``, but can be overwritten in a lab config.
        """
        p = linux.Path(self, "/tmp/tbot-wd")
        # Only create workdir once
        if not hasattr(self, "_wd_marker"):
            if not p.exists():
                self.exec0("mkdir", "-p", p)
            setattr(self, "_wd_marker", None)
        return p

    @property
    def username(self) -> str:
        """Return the name of the user running TBot."""
        return getpass.getuser()

    def __init__(self) -> None:
        """Create a new instance of a LocalLabHost."""
        super().__init__()
        self.channel = channel.SubprocessChannel()

    def destroy(self) -> None:
        """Destroy this instance of a LocalLabHost."""
        self.channel.close()

    def _obtain_channel(self) -> channel.Channel:
        return self.channel

    def _new_channel(self) -> channel.Channel:
        return channel.SubprocessChannel()
