from typing import Optional

import tbot.error

from . import channel


class NullChannelIO(channel.ChannelIO):
    def __init__(self) -> None:
        self._closed = False

    def write(self, buf: bytes) -> int:
        raise tbot.error.TbotException("Cannot write to a NULL channel")

    def read(self, n: int, timeout: Optional[float] = None) -> bytes:
        raise tbot.error.TbotException("Cannot read from a NULL channel")

    def close(self) -> None:
        self._closed = True

    def fileno(self) -> int:
        raise tbot.error.TbotException("NULL channel has no fileno")

    @property
    def closed(self) -> bool:
        return self._closed

    def update_pty(self, columns: int, lines: int) -> None:
        pass


class NullChannel(channel.Channel):
    def __init__(self) -> None:
        super().__init__(NullChannelIO())
