import typing
import shlex
import tbot
from . import machine
from . import board
from tbot.machine import linux

B = typing.TypeVar("B", bound=board.Board)


class UBootMachine(machine.BoardMachine, tbot.machine.InteractiveMachine, typing.Generic[B]):
    autoboot_prompt = r"Hit any key to stop autoboot:\s+\d+\s+"
    autoboot_keys = "\n"
    prompt = "U-Boot> "

    def __init__(self, board: B) -> None:
        super().__init__(board)

        self.channel = self.connect()

        with board.ev:
            self.channel.read_until_prompt(
                self.autoboot_prompt, regex=True, stream=board.ev
            )
        self.channel.send(self.autoboot_keys)
        self.channel.read_until_prompt(self.prompt)

    def destroy(self) -> None:
        self.channel.close()

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

    def interactive(self) -> None:
        tbot.log.message("Entering interactive shell (CTRL+D to exit) ...")

        self.channel.send(" \n")
        self.channel.attach_interactive()

        self.channel.send(" \n")
        try:
            self.channel.read_until_prompt(self.prompt, timeout=0.5)
        except TimeoutError:
            raise RuntimeError("Failed to reacquire U-Boot after interactive session!")

        tbot.log.message("Exiting interactive shell ...")
