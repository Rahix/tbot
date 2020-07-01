import abc
import os
import typing

import tbot.error
from tbot.machine import channel, connector, linux

try:
    import serial
except ImportError:
    raise tbot.error.TbotException(
        """\
The PyserialConnector requires pyserial to be installed:

    pip3 install pyserial"""
    )

__all__ = ("PyserialConnector",)

READ_CHUNK_SIZE = 4096

_AnyPath = typing.Union[str, os.PathLike]


class PyserialChannelIO(channel.ChannelIO):
    def __init__(self, port: _AnyPath, baudrate: int) -> None:
        self.serial = serial.Serial(os.fspath(port), baudrate=baudrate, exclusive=True)
        self.serial.timeout = 0

    def write(self, buf: bytes) -> int:
        if self.closed:
            raise channel.ChannelClosedException()

        channel.channel._debug_log(self, buf, True)
        self.serial.write(buf)
        return len(buf)

    def read(self, n: int, timeout: typing.Optional[float] = None) -> bytes:
        if self.closed:
            raise channel.ChannelClosedException()

        try:
            # Block for the first byte only
            self.serial.timeout = timeout
            first = self.serial.read(1)

            if first == b"":
                raise TimeoutError()

            assert len(first) == 1, f"Result is longer than expected ({first!r})!"
        finally:
            self.serial.timeout = 0

        remaining = b""
        if n > 1:
            # If there is more, read it now (non-blocking)
            remaining = self.serial.read(min(n, READ_CHUNK_SIZE) - 1)

        return channel.channel._debug_log(self, first + remaining, False)

    def close(self) -> None:
        if self.closed:
            raise channel.ChannelClosedException()

        self.serial.close()

    def fileno(self) -> int:
        return self.serial.fileno()

    @property
    def closed(self) -> bool:
        return not self.serial.is_open

    def update_pty(self, columns: int, lines: int) -> None:
        tbot.log.warning("Cannot update pty for pyserial connections")


class PyserialChannel(channel.Channel):
    def __init__(self, port: _AnyPath, baudrate: int) -> None:
        super().__init__(PyserialChannelIO(port, baudrate))


class PyserialConnector(connector.Connector):
    """
    Connect to a console connected to **localhost** (i.e. the host tbot is
    running on) using `pyserial`_.

    **Example**:

    .. code-block:: python

        class MyBoard(pyserial.PyserialConnector, board.Board):
            serial_port = "/dev/ttyUSB0"
            baudrate = 57600
    """

    @property
    @abc.abstractmethod
    def serial_port(self) -> _AnyPath:
        """
        Serial port to connect to.  Keep in mind that this path is **not** on
        the lab-host but on the localhost.
        """
        raise tbot.error.AbstractMethodError()

    baudrate = 115200
    """
    Baudrate of the serial line.
    """

    def __init__(self, host: typing.Optional[linux.LinuxShell] = None) -> None:
        if not isinstance(host, connector.SubprocessConnector):
            raise tbot.error.TbotException(
                "PyserialConnector can only use a localhost host (got {host!r})!"
            )
        self.host = host

    def _connect(self) -> channel.Channel:
        return PyserialChannel(self.serial_port, self.baudrate)

    def clone(self) -> typing.NoReturn:
        raise tbot.error.TbotException("Can't clone a (py)serial connection")
