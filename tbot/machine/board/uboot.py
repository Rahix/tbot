import typing
import tbot
from . import machine


class UBootMachine(machine.BoardMachine, typing.Generic[machine.B]):
    autoboot_prompt = r"Hit any key to stop autoboot:\s+\d+\s+"
    autoboot_keys = "\n"
    prompt = "U-Boot> "

    def __init__(self, board: machine.B) -> None:
        super().__init__(board)

        self.channel.read_until_prompt(self.autoboot_prompt, regex=True, stream=board.ev)
        self.channel.send(self.autoboot_keys)
        self.channel.read_until_prompt(self.prompt)

    def tmp_cmd(self, cmd: str) -> str:
        ev = tbot.log.command(self.name, cmd)
        ev.prefix = "   >> "
        return self.channel.raw_command(cmd, prompt=self.prompt, stream=ev)
