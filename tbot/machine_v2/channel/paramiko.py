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

import paramiko
import socket
import typing

from . import channel


class ParamikoChannelIO(channel.ChannelIO):
    __slots__ = ("ch",)

    def __init__(self, ch: paramiko.Channel) -> None:
        self.ch = ch

        self.ch.get_pty("xterm-256color", 80, 25, 1024, 1024)
        self.ch.invoke_shell()

    def write(self, buf: bytes) -> None:
        if self.closed:
            raise channel.ChannelClosedException()

        length = len(buf)
        cursor = 0
        while cursor < length:
            bytes_written = self.ch.send(buf[cursor:])
            if bytes_written == 0:
                raise Exception("closed")
            cursor += bytes_written

    def read(self, max: int = -1, timeout: typing.Optional[float] = None) -> bytes:
        if timeout is not None:
            self.ch.settimeout(timeout)

        try:
            max_read = min(1024, max) if max > 0 else 1024
            buf = self.ch.recv(max_read)

            while self.ch.recv_ready():
                max_read = min(1024, max - len(buf)) if max else 1024
                if max_read == 0:
                    break

                new = self.ch.recv(max_read)
                buf += new
        except socket.timeout:
            raise TimeoutError()
        finally:
            if timeout is not None:
                self.ch.settimeout(None)

        return buf

    def close(self) -> None:
        if self.closed:
            raise channel.ChannelClosedException()

        self.ch.close()

    def fileno(self) -> int:
        return self.ch.fileno()

    @property
    def closed(self) -> bool:
        return self.ch.exit_status_ready()
