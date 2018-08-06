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

    def send(self, d: str) -> None:
        raise NotImplementedError()

    def recv(self) -> str:
        raise NotImplementedError()

    def close(self) -> None:
        self.p.kill()
