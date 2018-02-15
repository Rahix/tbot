"""
Abstract base class for board machines
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
"""
import tbot

from . import machine


#pylint: disable=abstract-method
class MachineBoard(machine.Machine):
    """ Abstract base class for board machines """
    def __init__(self) -> None:
        super().__init__()
        self.boardname = None
        self.powerup = True

    def _setup(self, tb: 'tbot.TBot') -> None:
        super()._setup(tb)
        self.boardname = self.boardname or tb.config["board.name", "unknown"]

        if self.powerup:
            ev = tbot.logger.CustomLogEvent(
                ["board", "powerup"],
                stdout=f"\x1B[1mBOARD POWERUP\x1B[0m ({self.boardname})",
                verbosity=tbot.logger.Verbosity.INFO,
                dict_values={"board": self.boardname})

            tb.log.log(ev)

    def _destruct(self, tb: 'tbot.TBot') -> None:
        super()._destruct(tb)
        ev = tbot.logger.CustomLogEvent(
            ["board", "poweroff"],
            stdout=f"\x1B[1mBOARD POWEROFF\x1B[0m ({self.boardname})",
            verbosity=tbot.logger.Verbosity.INFO,
            dict_values={"board": self.boardname})
        tb.log.log(ev)

    @property
    def common_machine_name(self) -> str:
        """ Common name of this machine, for boards this will always be ``"board"`` """
        return "board"
