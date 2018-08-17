import typing
import shlex
import tbot
from . import machine
from . import board
from tbot.machine import linux

B = typing.TypeVar("B", bound=board.Board)


class UBootMachine(machine.BoardMachine, typing.Generic[B]):
    autoboot_prompt = r"Hit any key to stop autoboot:\s+\d+\s+"
    autoboot_keys = "\n"
    prompt = "U-Boot> "

    def __init__(self, board: B) -> None:
        super().__init__(board)

        with board.ev:
            self.channel.read_until_prompt(
                self.autoboot_prompt, regex=True, stream=board.ev
            )
        self.channel.send(self.autoboot_keys)
        self.channel.read_until_prompt(self.prompt)

    def build_command(self, *args: typing.Union[str, linux.Path[linux.LabHost]]) -> str:
        command = ""
        for arg in args:
            if isinstance(arg, linux.Path):
                arg = arg.relative_to("/tftpboot")._local_str()

            command += f"{shlex.quote(arg)} "

        return command[:-1]

    def exec(self, *args: typing.Union[str, linux.Path[linux.LabHost]]) -> typing.Tuple[int, str]:
        command = self.build_command(*args)

        with tbot.log.command(self.name, command) as ev:
            ev.prefix = "   >> "
            ret, out = self.channel.raw_command_with_retval(command, prompt=self.prompt, stream=ev)

        return ret, out

    def exec0(self, *args: typing.Union[str, linux.Path[linux.LabHost]]) -> str:
        ret, out = self.exec(*args)

        if ret != 0:
            raise tbot.machine.CommandFailedException(self, self.build_command(*args), out)

        return out
