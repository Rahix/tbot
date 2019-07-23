import abc
import typing
from . import machine


class Shell(machine.Machine):
    @abc.abstractmethod
    def _init_shell(self) -> typing.ContextManager:
        raise NotImplementedError("abstract method")

    @abc.abstractmethod
    def exec(self, *args: typing.Any) -> typing.Any:
        raise NotImplementedError("abstract method")
