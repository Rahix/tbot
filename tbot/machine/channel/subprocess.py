import time
import fcntl
import os
import subprocess
from tbot.machine import channel


class SubprocessChannel(channel.Channel):
    def __init__(self) -> None:
        self.p = subprocess.Popen(
            ["bash", "--norc", "-i"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

        # Make stdout nonblocking
        flags = fcntl.fcntl(self.p.stdout, fcntl.F_GETFL)
        flags = flags | os.O_NONBLOCK
        fcntl.fcntl(self.p.stdout, fcntl.F_SETFL, flags)

        super().__init__()

    def send(self, data: str) -> None:
        self.p.stdin.write(data.encode("utf-8"))
        self.p.stdin.flush()

    def recv(self) -> str:
        buf = b""

        while buf == b"":
            new = self.p.stdout.read()
            if new is not None:
                buf = new
            time.sleep(0.1)

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
