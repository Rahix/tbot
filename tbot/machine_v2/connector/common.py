import contextlib
import typing

import tbot
from .. import channel, machine
from . import connector

SelfSubprocess = typing.TypeVar("SelfSubprocess", bound="SubprocessConnector")


class SubprocessConnector(connector.Connector):
    __slots__ = ()

    def _connect(self) -> channel.Channel:
        tbot.log.message("--> connecting")
        return channel.SubprocessChannel()

    def clone(self: SelfSubprocess) -> SelfSubprocess:
        tbot.log.message("--> subp clone")
        return type(self)()


SelfSerial = typing.TypeVar("SelfSerial", bound="SerialConsoleConnector")


class SerialConsoleConnector(connector.Connector):
    __slots__ = ("mach",)

    def __init__(self, mach: machine.Machine) -> None:
        self.mach = mach

    @contextlib.contextmanager
    def _connect(self) -> typing.Iterator[channel.Channel]:
        tbot.log.message("--> serial connecting start")
        with self.mach.clone() as cloned:
            ch = cloned.ch.take()
            tbot.log.message("--> serial connecting")
            ch.sendline("picocom -b 115200 /dev/ttyUSB0")
            yield ch

    def clone(self: SelfSerial) -> SelfSerial:
        raise NotImplementedError("can't clone a serial connection")
