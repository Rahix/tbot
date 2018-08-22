import abc
import time
import typing
import tbot
from tbot.machine import board
from tbot.machine import linux
from tbot.machine import channel

B = typing.TypeVar("B", bound=board.Board)
Self = typing.TypeVar("Self", bound="LinuxMachine")


class LinuxMachine(board.BoardMachine[B], linux.LinuxMachine):
    login_prompt = "login: "
    login_timeout = 1.0

    # Most boards use busybox which has ash built-in
    shell = "ash"

    @property
    def name(self) -> str:
        return self.board.name + "-linux"

    @property
    def workdir(self: Self) -> "linux.Path[Self]":
        return linux.Path(self, "/tmp")

    @property
    @abc.abstractmethod
    def password(self) -> typing.Optional[str]:
        pass

    @abc.abstractmethod
    def __init__(self, b: typing.Union[B, board.UBootMachine[B]]) -> None:
        super().__init__(b.board if isinstance(b, board.UBootMachine) else b)

    def boot_to_shell(self) -> None:
        chan = self._obtain_channel()

        with tbot.log.EventIO(tbot.log.c("LINUX BOOT").bold + f" ({self.name})") as ev:
            ev.prefix = "   <> "
            chan.read_until_prompt(self.login_prompt, stream=ev)

        chan.send(self.username + "\n")
        if self.password is not None:
            chan.read_until_prompt("word: ")
            chan.send(self.password + "\n")
        time.sleep(self.login_timeout)
        chan.initialize(shell=self.shell)


class LinuxWithUBootMachine(LinuxMachine[B]):
    boot_command = "run bootcmd"

    @property
    @abc.abstractmethod
    def uboot(self) -> typing.Type[board.UBootMachine[B]]:
        pass

    def __init__(self, b: typing.Union[B, board.UBootMachine[B]]) -> None:
        super().__init__(b)
        if isinstance(b, board.UBootMachine):
            self.ub = None
            self.channel = b.channel
        else:
            self.ub = self.uboot(b)
            self.channel = self.ub.channel

        self.channel.send(self.boot_command + "\n")
        self.boot_to_shell()

    def destroy(self) -> None:
        if self.ub is not None:
            self.ub.destroy()

    def _obtain_channel(self) -> channel.Channel:
        return self.channel


class LinuxStandaloneMachine(LinuxMachine[B]):

    def __init__(self, b: typing.Union[B, board.UBootMachine[B]]) -> None:
        super().__init__(b)
        if isinstance(b, board.UBootMachine):
            raise RuntimeError(f"{self!r} does not support booting from UBoot")

        if self.board.channel is not None:
            self.channel = self.board.channel
        else:
            raise RuntimeError("{board!r} does not support a serial connection!")

        self.boot_to_shell()

    def destroy(self) -> None:
        self.channel.close()

    def _obtain_channel(self) -> channel.Channel:
        return self.channel
