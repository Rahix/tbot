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

import fcntl
import os
import pty
import select
import subprocess
import time
import typing
from tbot import log
from . import channel


class SubprocessChannel(channel.Channel):
    """Subprocess based channel."""

    def __init__(self) -> None:
        """Create a new :mod:`subprocess` based channel."""
        self.pty_master, pty_slave = pty.openpty()

        self.p = subprocess.Popen(
            ["bash", "--norc", "-i"],
            stdin=pty_slave,
            stdout=pty_slave,
            stderr=pty_slave,
            start_new_session=True,
        )

        flags = fcntl.fcntl(self.pty_master, fcntl.F_GETFL)
        flags = flags | os.O_NONBLOCK
        fcntl.fcntl(self.pty_master, fcntl.F_SETFL, flags)

        super().__init__()

    def send(self, data: typing.Union[bytes, str]) -> None:  # noqa: D102
        self.p.poll()
        if self.p.returncode is not None:
            raise channel.ChannelClosedException()

        data = data if isinstance(data, bytes) else data.encode("utf-8")
        self._debug_log(data, True)

        length = len(data)
        c = 0
        while c < length:
            b = os.write(self.pty_master, data[c:])
            if b == 0:
                raise channel.ChannelClosedException()
            c += b

    def recv(
        self, timeout: typing.Optional[float] = None, max: typing.Optional[int] = None
    ) -> bytes:  # noqa: D102
        self.p.poll()

        buf = b""

        if self.p.returncode is None:
            # If the process is still running, wait for one byte or
            # the timeout to arrive
            r, _, _ = select.select([self.pty_master], [], [], timeout)
            if self.pty_master not in r:
                raise TimeoutError()
        # If the process has ended, check for anything left

        maxread = min(1024, max) if max else 1024
        try:
            buf = os.read(self.pty_master, maxread)
            self._debug_log(buf)
        except (BlockingIOError, OSError):
            # If we don't get anything, and the timeout hasn't triggered
            # this channel is closed
            raise channel.ChannelClosedException()

        try:
            while True:
                maxread = min(1024, max - len(buf)) if max else 1024
                if maxread == 0:
                    break
                new = os.read(self.pty_master, maxread)
                buf += new
                self._debug_log(new)
        except BlockingIOError:
            pass

        return buf

    def close(self) -> None:  # noqa: D102
        if self.isopen():
            self.cleanup()
        sid = os.getsid(self.p.pid)
        self.p.terminate()
        os.close(self.pty_master)
        self.p.wait()

        # Wait for all processes in the session to end.  Most of the time
        # this will return immediately, but in some cases (eg. a serial session
        # with picocom) we have to wait a bit until we can continue.  To be as
        # quick as possible this is implemented as exponential backoff and will
        # give up after 1 second (1.27 to be exact) and emit a warning.
        for t in range(7):
            if (
                subprocess.call(
                    ["ps", "-s", str(sid)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                != 0
            ):
                break
            time.sleep(2 ** t / 100)
        else:
            log.warning(
                "There are still processes running in this session.\n"
                "   Something might break."
            )

    def fileno(self) -> int:  # noqa: D102
        return self.pty_master

    def isopen(self) -> bool:  # noqa: D102
        self.p.poll()
        return self.p.returncode is None
