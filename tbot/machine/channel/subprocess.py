import typing
import pty
import os
import fcntl
import select
import subprocess
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
        except BlockingIOError:
            # If we don't get anything, and the timeout hasn't triggered
            # this channel is closed
            raise channel.ChannelClosedException()

        try:
            while True:
                maxread = min(1024, max - len(buf)) if max else 1024
                if maxread == 0:
                    break
                buf += os.read(self.pty_master, maxread)
        except BlockingIOError:
            pass

        return buf

    def close(self) -> None:  # noqa: D102
        if self.isopen():
            self.cleanup()
        self.p.kill()
        self.p.wait()

    def fileno(self) -> int:  # noqa: D102
        return self.pty_master

    def isopen(self) -> bool:  # noqa: D102
        self.p.poll()
        return self.p.returncode is None
