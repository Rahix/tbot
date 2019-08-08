import abc
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


SelfConsole = typing.TypeVar("SelfConsole", bound="ConsoleConnector")


class ConsoleConnector(connector.Connector):
    @abc.abstractmethod
    def connect(self, mach: linux.LinuxShell) -> typing.ContextManager[channel.Channel]:
        raise NotImplementedError("abstract method")

    def __init__(self, mach: linux.LinuxShell) -> None:
        self.host = mach

    @contextlib.contextmanager
    def _connect(self) -> typing.Iterator[channel.Channel]:
        with self.host.clone() as cloned, self.connect(cloned) as ch:
            yield ch
            # yield cloned.open_channel("picocom", "-b", str(115200), "/dev/ttyUSB0")

    def clone(self: SelfConsole) -> SelfConsole:
        raise NotImplementedError("can't clone a serial connection")
