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

import shutil
import socket
import typing
import paramiko
from . import channel


class ParamikoChannel(channel.Channel):
    """Paramiko based channel."""

    def __init__(self, ch: paramiko.Channel) -> None:
        """
        Create a new TBot channel based on a Paramiko channel.

        :param paramiko.Channel ch: Paramiko Channel
        """
        self.ch = ch

        self.ch.get_pty("xterm-256color", 80, 25, 1024, 1024)
        self.ch.invoke_shell()

        super().__init__()

    def send(self, data: typing.Union[bytes, str]) -> None:  # noqa: D102
        if self.ch.exit_status_ready():
            raise channel.ChannelClosedException()

        data = data if isinstance(data, bytes) else data.encode("utf-8")

        length = len(data)
        c = 0
        while c < length:
            b = self.ch.send(data[c:])
            if b == 0:
                raise channel.ChannelClosedException()
            c += b

    def recv(
        self, timeout: typing.Optional[float] = None, max: typing.Optional[int] = None
    ) -> bytes:  # noqa: D102
        if timeout is not None:
            self.ch.settimeout(timeout)

        try:
            maxread = min(1024, max) if max else 1024
            buf = self.ch.recv(maxread)

            while self.ch.recv_ready():
                maxread = min(1024, max - len(buf)) if max else 1024
                if maxread == 0:
                    break
                buf += self.ch.recv(maxread)
        except socket.timeout:
            raise TimeoutError()
        finally:
            if timeout is not None:
                self.ch.settimeout(None)

        if buf == b"":
            raise channel.ChannelClosedException()

        return buf

    def close(self) -> None:  # noqa: D102
        if self.isopen():
            self.cleanup()
        self.ch.close()

    def fileno(self) -> int:  # noqa: D102
        return self.ch.fileno()

    def isopen(self) -> bool:  # noqa: D102
        return not self.ch.exit_status_ready()

    def _interactive_setup(self) -> None:  # noqa: D102
        size = shutil.get_terminal_size()
        self.ch.resize_pty(size.columns, size.lines, 1024, 1024)
        self.ch.settimeout(0.0)

    def _interactive_teardown(self) -> None:  # noqa: D102
        self.ch.settimeout(None)
