import typing
import shlex
import tbot
from tbot import machine
from tbot.machine import board
from tbot.machine import linux
from . import special

B = typing.TypeVar("B", bound=board.Board)


class UBootMachine(board.BoardMachine[B], machine.InteractiveMachine):
    r"""
    Generic U-Boot board machine.

    **Example implementation**::

        from tbot.machine import board

        class MyBoard(board.Board):
            ...

        class MyBoardUBoot(board.UBootMachine[MyBoard]):
            pass

        BOARD = MyBoard
        UBOOT = MyBoardUBoot

    .. py:attribute:: autoboot_prompt: str

        Regular expression of the autoboot prompt

    .. py:attribute:: autoboot_keys: str = "\\n"

        Keys that should be sent to intercept autoboot

    .. py:attribute:: prompt: str = "U-Boot> "

        U-Prompt that was configured when building U-Boot
    """

    autoboot_prompt = r"Hit any key to stop autoboot:\s+\d+\s+"
    autoboot_keys = "\n"
    prompt = "U-Boot> "

    @property
    def name(self) -> str:
        """Name of this U-Boot machine."""
        return self.board.name + "-uboot"

    def __init__(self, board: B) -> None:  # noqa: D107
        super().__init__(board)

        self.channel: machine.channel.Channel
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
        """Destroy this U-Boot machine."""
        self.channel.close()

    def build_command(
        self, *args: typing.Union[str, special.Special, linux.Path[linux.LabHost]]
    ) -> str:
        """
        Return the string representation of a command.

        :param args: Each argument can either be a :class:`str` or a special token
            like :class:`~tbot.machine.board.Env`.
        :rtype: str
        """
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
        """
        Run a command in U-Boot and check its return value.

        :param args: Each argument can either be a :class:`str` or a special token
            like :class:`~tbot.machine.board.Env`.
        :rtype: tuple[int, str]
        :returns: A tuple with the return code and output of the command
        """
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
        """
        Run a command in U-Boot and ensure its return value is zero.

        :param args: Each argument can either be a :class:`str` or a special token
            like :class:`~tbot.machine.board.Env`.
        :rtype: str
        :returns: The output of the command
        """
        ret, out = self.exec(*args)

        if ret != 0:
            raise tbot.machine.CommandFailedException(
                self, self.build_command(*args), out
            )

        return out

    def interactive(self) -> None:
        """
        Drop into an interactive U-Boot session.

        :raises RuntimeError: If TBot was not able to reacquire the shell
            after the session is over.
        """
        tbot.log.message("Entering interactive shell (CTRL+D to exit) ...")

        self.channel.send(" \n")
        self.channel.attach_interactive()

        self.channel.send(" \n")
        try:
            self.channel.read_until_prompt(self.prompt, timeout=0.5)
        except TimeoutError:
            raise RuntimeError("Failed to reacquire U-Boot after interactive session!")

        tbot.log.message("Exiting interactive shell ...")
