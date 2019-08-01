import contextlib
import typing

from .. import channel, linux
from . import connector

SelfSubprocess = typing.TypeVar("SelfSubprocess", bound="SubprocessConnector")


class SubprocessConnector(connector.Connector):
    __slots__ = ()

    def _connect(self) -> channel.Channel:
        return channel.SubprocessChannel()

    def clone(self: SelfSubprocess) -> SelfSubprocess:
        return type(self)()


SelfSerial = typing.TypeVar("SelfSerial", bound="SerialConsoleConnector")


class SerialConsoleConnector(connector.Connector):
    def __init__(self, mach: linux.LinuxShell) -> None:
        self.mach = mach

    @contextlib.contextmanager
    def _connect(self) -> typing.Iterator[channel.Channel]:
        with self.mach.clone() as cloned:
            yield cloned.open_channel("picocom", "-b", str(115200), "/dev/ttyUSB0")

    def clone(self: SelfSerial) -> SelfSerial:
        raise NotImplementedError("can't clone a serial connection")
