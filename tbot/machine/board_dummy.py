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
    """
    def __init__(self, turn_on: bool = True) -> None:
        self.name = "unknown"
        self.turn_on = turn_on

        self.power_cmd_on = ""
        self.power_cmd_off = ""

        self.noenv: typing.Optional[tbot.machine.Machine] = None

        super().__init__()

    def _setup(self, tb: 'tbot.TBot') -> None:
        super()._setup(tb)
        self.name = tb.config["board.shell.name", self.name]

        self.power_cmd_on = tb.config["board.power.on_command"]
        self.power_cmd_off = tb.config["board.power.off_command"]

        # Save the noenv shell to have it accessible later
        self.noenv = tb.machines["labhost-noenv"]

        if self.turn_on:
            self.noenv.exec0(self.power_cmd_on, log_show_stdout=False)

    def _destruct(self, tb: 'tbot.TBot') -> None:
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
