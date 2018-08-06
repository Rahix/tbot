import time
import pty
import os
import fcntl
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
        )

        flags = fcntl.fcntl(self.pty_master, fcntl.F_GETFL)
        flags = flags | os.O_NONBLOCK
        fcntl.fcntl(self.pty_master, fcntl.F_SETFL, flags)

        super().__init__()

    def send(self, data: str) -> None:
        os.write(self.pty_master, data.encode("utf-8"))

    def recv(self) -> str:
        buf = b""

        waiting = True
        while waiting:
            try:
                buf = os.read(self.pty_master, 1000)
            except BlockingIOError:
                time.sleep(0.1)
            else:
                waiting = False

        try:
            while True:
                buf += os.read(self.pty_master, 1000)
        except BlockingIOError:
            pass

        s: str
        try:
            s = buf.decode("utf-8")
        except UnicodeDecodeError:
            # Fall back to latin-1 if unicode decoding fails ... This is not perfect
            # but it does not stop a test run just because of an invalid character
            s = buf.decode("latin_1")

        return s

    def close(self) -> None:
        self.p.kill()
