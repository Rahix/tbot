import time
import paramiko
from . import channel


class ParamikoChannel(channel.Channel):
    def __init__(self, ch: paramiko.Channel) -> None:
        self.ch = ch

        self.ch.get_pty("xterm-256color")
        self.ch.resize_pty(200, 200, 1000, 1000)
        self.ch.invoke_shell()

        super().__init__()

    def send(self, data: str) -> None:
        if data == "":
            return

        data_bytes = data.encode("utf-8")
        length = len(data_bytes)
        c = 0
        while c < length:
            b = self.ch.send(data_bytes[c:])
            if b == 0:
                raise channel.ChannelClosedException()
            c += b

    def recv(self) -> str:
        # Wait until at least one byte is available
        while not self.ch.recv_ready():
            time.sleep(0.1)

        buf = b""
        while self.ch.recv_ready():
            buf = self.ch.recv(1000)

        if buf == b"":
            raise channel.ChannelClosedException()

        s: str
        try:
            s = buf.decode("utf-8")
        except UnicodeDecodeError:
            # Fall back to latin-1 if unicode decoding fails ... This is not perfect
            # but it does not stop a test run just because of an invalid character
            s = buf.decode("latin_1")

        return s

    def close(self) -> None:
        self.ch.close()
