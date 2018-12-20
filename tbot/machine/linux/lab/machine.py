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

import abc
import typing
import tbot
from tbot.machine import linux
from tbot.machine import channel
from tbot.machine.linux import special

Self = typing.TypeVar("Self", bound="LabHost")


class LabHost(linux.LinuxMachine):
    """Generic LabHost abstraction."""

    @abc.abstractmethod
    def _new_channel(self) -> channel.Channel:
        pass

    def new_channel(
        self: Self, *args: typing.Union[str, special.Special, linux.Path[Self]]
    ) -> channel.Channel:
        """
        Create a new channel for a new machine instance via this LabHost.

        If ``*args`` is non-empty, it is interpreted as a command that will be
        run on the LabHost to open a connection to the new machine. Once this
        command finished, the new channel will be closed.

        If ``*args`` is empty, a shell on the LabHost is opened, that you can
        run commands using eg. :meth:`~tbot.machine.channel.Channel.raw_command`.

        **Example**::

            with tbot.acquire_lab() as lh:
                bdi_ch = lh.new_channel("telnet", "bdi4")

                # Do something with the bdi
        """
        chan = self._new_channel()
        if args != ():
            cmd = self.build_command(*args)
            tbot.log_event.command(self.name, cmd)
            # Send exit after the command so this channel will close once it
            # is done.
            chan.send(cmd + " ; exit\n")
            # Read back the command we just sent
            chan.recv()
        return chan

    def build(self) -> linux.BuildMachine:
        raise KeyError("No build machine available!")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"

    @property
    def lh(self) -> "LabHost":
        return self
