import abc
import typing
from .. import channel, machine

Self = typing.TypeVar("Self", bound="Connector")


class Connector(machine.Machine):
    __slots__ = ()

    @abc.abstractmethod
    def _connect(self) -> typing.ContextManager[channel.Channel]:
        raise NotImplementedError("abstract method")

    @abc.abstractmethod
    def clone(self: Self) -> Self:
        raise NotImplementedError("abstract method")
