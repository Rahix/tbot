import abc
import contextlib
import typing
import tbot
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
            tbot.log.EventIO(
                ["board", "on", self.name],
                tbot.log.c("POWERON").bold + f" ({self.name})",
                verbosity=tbot.log.Verbosity.QUIET,
            )
            self.poweron()
            yield None
        finally:
            tbot.log.EventIO(
                ["board", "off", self.name],
                tbot.log.c("POWEROFF").bold + f" ({self.name})",
                verbosity=tbot.log.Verbosity.QUIET,
            )
            self.poweroff()
