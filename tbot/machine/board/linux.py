import abc
import time
import typing
import tbot
from tbot.machine import board
from tbot.machine import linux
from tbot.machine import channel
from . import special

B = typing.TypeVar("B", bound=board.Board)
Self = typing.TypeVar("Self", bound="LinuxMachine")


class LinuxMachine(linux.LinuxMachine, board.BoardMachine[B]):
    login_prompt = "login: "
    login_timeout = 1.0

    # Most boards use busybox which has ash built-in
    shell: typing.Type[linux.shell.Shell] = linux.shell.Ash

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

    def boot_to_shell(self, stream: typing.TextIO) -> None:
        chan = self._obtain_channel()

        chan.read_until_prompt(self.login_prompt, stream=stream)

        chan.send(self.username + "\n")
        stream.write(self.login_prompt + self.username + "\n")
        if self.password is not None:
            chan.read_until_prompt("word: ")
            stream.write("Password: ****")
            chan.send(self.password + "\n")
        time.sleep(self.login_timeout)
        chan.initialize(sh=self.shell)


class LinuxWithUBootMachine(LinuxMachine[B]):
    boot_commands: typing.List[typing.List[typing.Union[str, special.Special]]] = [
        ["run", "bootcmd"]
    ]

    @property
    @abc.abstractmethod
    def uboot(self) -> typing.Type[board.UBootMachine[B]]:
        pass

    def __init__(self, b: typing.Union[B, board.UBootMachine[B]]) -> None:
        super().__init__(b)
        if isinstance(b, board.UBootMachine):
            ub = b
            self.ub = None
            self.channel = b.channel
        else:
            self.ub = self.uboot(b)
            ub = self.ub
            self.channel = self.ub.channel

        tbot.log.EventIO(tbot.log.c("LINUX BOOT").bold + f" ({self.name})")
        for cmd in self.boot_commands[:-1]:
            ub.exec0(*cmd)

        # Make it look like a normal U-Boot command
        last_command = ub.build_command(*self.boot_commands[-1])
        with tbot.log.command(ub.name, last_command) as ev:
            ev.prefix = "   <> "
            self.channel.send(last_command + "\n")
            self.boot_to_shell(channel.channel.SkipStream(ev, len(last_command) + 1))

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

        with tbot.log.EventIO(tbot.log.c("LINUX BOOT").bold + f" ({self.name})") as ev:
            ev.prefix = "   <> "
            self.boot_to_shell(ev)

    def destroy(self) -> None:
        self.channel.close()

    def _obtain_channel(self) -> channel.Channel:
        return self.channel
