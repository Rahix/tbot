"""
Abstract base class for board machines
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
"""
import typing
import tbot

from . import machine


#pylint: disable=abstract-method
class MachineBoard(machine.Machine):
    """ Abstract base class for board machines """
    def __init__(self) -> None:
        super().__init__()
        self.boardname = None
        self.powerup = True
        self._tb: typing.Optional['tbot.TBot'] = None

    def _setup(self,
               tb: 'tbot.TBot',
               previous: typing.Optional[machine.Machine] = None,
              ) -> 'MachineBoard':
        super()._setup(tb, previous)
        self.boardname = self.boardname or tb.config["board.name", "unknown"]
        self._tb = tb

        if self.powerup:
            ev = tbot.logger.CustomLogEvent(
                ["board", "powerup"],
                stdout=f"\x1B[1mBOARD POWERUP\x1B[0m ({self.boardname})",
                verbosity=tbot.logger.Verbosity.INFO,
                dict_values={"board": self.boardname})

            tb.log.log(ev)
        return self

    def _destruct(self, tb: 'tbot.TBot') -> None:
        super()._destruct(tb)
        ev = tbot.logger.CustomLogEvent(
            ["board", "poweroff"],
            stdout=f"\x1B[1mBOARD POWEROFF\x1B[0m ({self.boardname})",
            verbosity=tbot.logger.Verbosity.INFO,
            dict_values={"board": self.boardname})
        tb.log.log(ev)

    def powercycle(self) -> None:
        """ Powercycle the board """
        if not isinstance(self._tb, tbot.TBot):
            raise Exception("Board machine not initialized correctly, board might still be on!")
        self._destruct(self._tb)
        self._setup(self._tb, self)

    @property
    def common_machine_name(self) -> str:
        """ Common name of this machine, for boards this will always be ``"board"`` """
        return "board"
