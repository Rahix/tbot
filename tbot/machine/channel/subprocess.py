import typing
import pty
import os
import fcntl
import select
import subprocess
from . import channel


class SubprocessChannel(channel.Channel):

    def __init__(self) -> None:
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

    def send(self, data: typing.Union[bytes, str]) -> None:
        if self.p.returncode is not None:
            raise channel.ChannelClosedException()

        data = data if isinstance(data, bytes) else data.encode("utf-8")

        length = len(data)
        c = 0
        while c < length:
            b = os.write(self.pty_master, data[c:])
            if b == 0:
                raise channel.ChannelClosedException()
            c += b

    def recv(self) -> bytes:
        if self.p.returncode is not None:
            raise channel.ChannelClosedException()

        buf = b""

        r, _, _ = select.select([self.pty_master], [], [])
        if self.pty_master in r:
            buf = os.read(self.pty_master, 1024)

        try:
            while True:
                buf += os.read(self.pty_master, 1024)
        except BlockingIOError:
            pass

        return buf

    def close(self) -> None:
        self.p.kill()
        self.p.wait()

    def fileno(self) -> int:
        return self.pty_master
