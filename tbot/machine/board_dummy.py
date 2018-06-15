"""
Board machine dummy for just turning the board on and off
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
"""
import typing
import pathlib
import tbot
from . import machine
from . import board


class MachineBoardDummy(board.MachineBoard):
    """
    Board machine dummy for just turning the board on and off

    :param turn_on: Whether to turn on the board or just turn it off in the end.
        Useful for example for the U-Boot test suite which expects the board to
        be off in the beginning but still needs a manual poweroff once it's done.
    :type turn_on: bool
    :param power_cmd_on: The command for turning on the board, defaults to
                         ``tb.config["board.power.on_command"]``
    :type power_cmd_on: str
    :param power_cmd_off: The command for turning off the board, defaults to
                          ``tb.config["board.power.off_command"]``
    :type power_cmd_off: str
    """

    def __init__(
        self,
        *,
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

    def _setup(
        self, tb: "tbot.TBot", previous: typing.Optional[machine.Machine] = None
    ) -> "MachineBoardDummy":
        self.name = self.name or tb.config["board.name", "unknown"]
        if not isinstance(self.name, str):
            raise Exception(f"Invalid name: {self.name!r}")
        self.boardname = self.name
        super()._setup(tb, previous)

        self.power_cmd_on = self.power_cmd_on or tb.config["board.power.on_command"]
        self.power_cmd_off = self.power_cmd_off or tb.config["board.power.off_command"]

        # Save the noenv shell to have it accessible later
        self.noenv = tb.machines["labhost-noenv"]

        if self.noenv is None:
            raise Exception("no-env shell does not exist")

        if self.powerup:
            self.noenv.exec0(self.power_cmd_on, log_show_stdout=False)

        return self

    def _destruct(self, tb: "tbot.TBot") -> None:
        super()._destruct(tb)
        if isinstance(self.noenv, tbot.machine.Machine) and isinstance(
            self.power_cmd_off, str
        ):
            self.noenv.exec0(self.power_cmd_off, log_show_stdout=False)
        else:
            raise Exception(
                "noenv shell not initialized correctly, board might still be on!"
            )

    def _exec(
        self, command: str, stdout_handler: typing.Optional[tbot.log.LogStdoutHandler]
    ) -> typing.Tuple[int, str]:
        raise Exception("Cannot execute commands on a dummy board machine")

    @property
    def workdir(self) -> pathlib.PurePosixPath:
        raise Exception("A dummy board does not have a workdir")

    @property
    def unique_machine_name(self) -> str:
        """ Unique name of this machine, ``"board-dummy-<boardshell-name>"`` """
        return f"board-dummy-{self.name}"
