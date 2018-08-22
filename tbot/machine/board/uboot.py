import typing
import shlex
import tbot
from tbot import machine
from tbot.machine import board
from tbot.machine import linux
from . import special

B = typing.TypeVar("B", bound=board.Board)


class UBootMachine(board.BoardMachine[B], machine.InteractiveMachine):
    autoboot_prompt = r"Hit any key to stop autoboot:\s+\d+\s+"
    autoboot_keys = "\n"
    prompt = "U-Boot> "

    @property
    def name(self) -> str:
        return self.board.name + "-uboot"

    def __init__(self, board: B) -> None:
        super().__init__(board)

        if board.channel is not None:
            self.channel = board.channel
        else:
            raise RuntimeError("{board!r} does not support a serial connection!")

        with board.boot_ev:
            self.channel.read_until_prompt(
                self.autoboot_prompt, regex=True, stream=board.boot_ev
            )
        self.channel.send(self.autoboot_keys)
        self.channel.read_until_prompt(self.prompt)

    def destroy(self) -> None:
        self.channel.close()

    def build_command(
        self, *args: typing.Union[str, special.Special, linux.Path[linux.LabHost]]
    ) -> str:
        command = ""
        for arg in args:
            if isinstance(arg, linux.Path):
                arg = arg.relative_to("/tftpboot")._local_str()

            if isinstance(arg, special.Special):
                command += arg.resolve_string() + " "
            else:
                command += f"{shlex.quote(arg)} "

        return command[:-1]

    def exec(
        self, *args: typing.Union[str, special.Special, linux.Path[linux.LabHost]]
    ) -> typing.Tuple[int, str]:
        command = self.build_command(*args)

        with tbot.log.command(self.name, command) as ev:
            ev.prefix = "   >> "
            ret, out = self.channel.raw_command_with_retval(
                command, prompt=self.prompt, stream=ev
            )

        return ret, out

    def exec0(
        self, *args: typing.Union[str, special.Special, linux.Path[linux.LabHost]]
    ) -> str:
        ret, out = self.exec(*args)

        if ret != 0:
            raise tbot.machine.CommandFailedException(
                self, self.build_command(*args), out
            )

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
