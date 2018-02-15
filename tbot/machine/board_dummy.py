"""
Board machine dummy for just turning the board on and off
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
"""
import typing
import tbot
from . import board

class MachineBoardDummy(board.MachineBoard):
    """
    Board machine dummy for just turning the board on and off

    :param turn_on: Whether to turn on the board or just turn it off in the end.
        Useful for example for the U-Boot test suite which expects the board to
        be off in the beginning but still needs a manual poweroff once it's done.
    :param power_cmd_on: The command for turning on the board, defaults to
                         ``tb.config["board.power.on_command"]``
    :param power_cmd_off: The command for turning off the board, defaults to
                          ``tb.config["board.power.off_command"]``
    """
    def __init__(self, *,
                 name: typing.Optional[str] = None,
                 turn_on: bool = True,
                 power_cmd_on: typing.Optional[str] = None,
                 power_cmd_off: typing.Optional[str] = None,
                ) -> None:
        super().__init__()
        self.name = name
        self.powerup = turn_on

        self.power_cmd_on = power_cmd_on
        self.power_cmd_off = power_cmd_off

        self.noenv: typing.Optional[tbot.machine.Machine] = None


    def _setup(self, tb: 'tbot.TBot') -> None:
        self.name = self.name or tb.config["board.name", "unknown"]
        self.boardname = self.name
        super()._setup(tb)

        self.power_cmd_on = self.power_cmd_on or tb.config["board.power.on_command"]
        self.power_cmd_off = self.power_cmd_off or tb.config["board.power.off_command"]

        # Save the noenv shell to have it accessible later
        self.noenv = tb.machines["labhost-noenv"]

        if self.powerup:
            self.noenv.exec0(self.power_cmd_on, log_show_stdout=False)

    def _destruct(self, tb: 'tbot.TBot') -> None:
        super()._destruct(tb)
        if isinstance(self.noenv, tbot.machine.Machine):
            self.noenv.exec0(self.power_cmd_off, log_show_stdout=False)
        else:
            raise Exception("noenv shell not initialized correctly, board might still be on!")

    def _exec(self,
              command: str,
              log_event: tbot.logger.LogEvent) -> typing.Tuple[int, str]:
        raise Exception("Cannot execute commands on a dummy board machine")

    @property
    def unique_machine_name(self) -> str:
        """ Unique name of this machine, ``"board-dummy-<boardshell-name>"`` """
        return f"board-dummy-{self.name}"
