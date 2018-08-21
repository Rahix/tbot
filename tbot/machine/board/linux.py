import abc
import time
import typing
import tbot
from tbot.machine import linux
from tbot.machine import channel
from . import machine
from . import uboot
from . import board

B = typing.TypeVar("B", bound=board.Board)
Self = typing.TypeVar("Self", bound="LinuxMachine")


class LinuxMachine(machine.BoardMachine, linux.LinuxMachine, typing.Generic[B]):
    boot_command = "run bootcmd"
    login_prompt = "login: "
    login_timeout = 1.0

    # Most boards use busybox which has ash built-in
    shell = "ash"

    @property
    def workdir(self: Self) -> "linux.Path[Self]":
        return linux.Path(self, "/tmp")

    @property
    @abc.abstractmethod
    def password(self) -> str:
        pass

    @abc.abstractmethod
    def __init__(self, b: typing.Union[B, uboot.UBootMachine[B]]) -> None:
        super().__init__(b.board if isinstance(b, uboot.UBootMachine) else b)

    def boot_to_shell(self) -> None:
        chan = self._obtain_channel()

        with tbot.log.EventIO(tbot.log.c("LINUX BOOT").bold + f" ({self.name})") as ev:
            ev.prefix = "   <> "
            chan.read_until_prompt(self.login_prompt, stream=ev)

        chan.send(self.username + "\n")
        chan.read_until_prompt("word: ")
        chan.send(self.password + "\n")
        time.sleep(self.login_timeout)
        chan.initialize(shell=self.shell)


class LinuxWithUBootMachine(LinuxMachine, typing.Generic[B]):
    @abc.abstractmethod
    def init_uboot(self, board: B) -> uboot.UBootMachine[B]:
        pass

    def __init__(self, b: typing.Union[B, uboot.UBootMachine[B]]) -> None:
        super().__init__(b)
        if isinstance(b, uboot.UBootMachine):
            self.ub = None
            self.channel = b.channel
        else:
            self.ub = self.init_uboot(b)
            self.channel = self.ub.channel

        self.channel.send(self.boot_command + "\n")
        self.boot_to_shell()

    def destroy(self) -> None:
        if self.ub is not None:
            self.ub.destroy()

    def _obtain_channel(self) -> channel.Channel:
        return self.channel


class LinuxStandaloneMachine(LinuxMachine, typing.Generic[B]):
    def __init__(self, b: typing.Union[B, uboot.UBootMachine[B]]) -> None:
        super().__init__(b)
        if isinstance(b, uboot.UBootMachine):
            raise RuntimeError(f"{self!r} does not support booting from UBoot")

        self.channel = self.connect()

        self.boot_to_shell()

    def destroy(self) -> None:
        self.channel.close()

    def _obtain_channel(self) -> channel.Channel:
        return self.channel
