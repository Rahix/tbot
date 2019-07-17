import abc
import contextlib
import typing
from .. import machine


class PowerControl(machine.Initializer):
    @abc.abstractmethod
    def poweron(self) -> None:
        pass

    @abc.abstractmethod
    def poweroff(self) -> None:
        pass

    @contextlib.contextmanager
    def _init_machine(self) -> typing.Iterator:
        try:
            self.poweron()
            yield None
        finally:
            self.poweroff()
