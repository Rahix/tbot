import typing
import shutil
import paramiko
from . import channel


class ParamikoChannel(channel.Channel):

    def __init__(self, ch: paramiko.Channel) -> None:
        self.ch = ch

        self.ch.get_pty("xterm-256color", 80, 25, 1024, 1024)
        self.ch.invoke_shell()

        super().__init__()

    def send(self, data: typing.Union[bytes, str]) -> None:
        data = data if isinstance(data, bytes) else data.encode("utf-8")

        length = len(data)
        c = 0
        while c < length:
            b = self.ch.send(data[c:])
            if b == 0:
                raise channel.ChannelClosedException()
            c += b

    def recv(self) -> bytes:
        buf = self.ch.recv(1024)

        while self.ch.recv_ready():
            buf += self.ch.recv(1024)

        if buf == b"":
            raise channel.ChannelClosedException()

        return buf

    def close(self) -> None:
        self.ch.close()

    def fileno(self) -> int:
        return self.ch.fileno()

    def _interactive_setup(self) -> None:
        size = shutil.get_terminal_size()
        self.ch.resize_pty(size.columns, size.lines, 1024, 1024)
        self.ch.settimeout(0.0)

    def _interactive_teardown(self) -> None:
        self.ch.settimeout(None)
