"""
Abstract base class for board machines
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
"""
import typing
import tbot

from . import machine

RST = tbot.log.has_color("0")
BOLD = tbot.log.has_color("1")


# pylint: disable=abstract-method
class MachineBoard(machine.Machine):
    """ Abstract base class for board machines """

    def __init__(self) -> None:
        super().__init__()
        self.boardname = None
        self.powerup = True
        self._tb: typing.Optional["tbot.TBot"] = None

    def _setup(
        self, tb: "tbot.TBot", previous: typing.Optional[machine.Machine] = None
    ) -> "MachineBoard":
        super()._setup(tb, previous)
        self.boardname = self.boardname or tb.config["board.name", "unknown"]
        self._tb = tb

        if self.powerup:
            tbot.log.event(
                ty=["board", "powerup"],
                msg=f"{BOLD}BOARD POWERUP{RST} ({self.boardname})",
                verbosity=tbot.log.Verbosity.INFO,
                dct={"board": self.boardname},
            )

        return self

    def _destruct(self, tb: "tbot.TBot") -> None:
        super()._destruct(tb)
        tbot.log.event(
            ty=["board", "poweroff"],
            msg=f"{BOLD}BOARD POWEROFF{RST} ({self.boardname})",
            verbosity=tbot.log.Verbosity.INFO,
            dct={"board": self.boardname},
        )

    def powercycle(self) -> None:
        """ Powercycle the board """
        if not isinstance(self._tb, tbot.TBot):
            raise Exception(
                "Board machine not initialized correctly, board might still be on!"
            )
        self._destruct(self._tb)
        self._setup(self._tb, self)

    @property
    def common_machine_name(self) -> str:
        """ Common name of this machine, for boards this will always be ``"board"`` """
        return "board"
