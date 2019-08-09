import abc
import contextlib
import typing

import tbot
from .. import machine, board, channel, connector


class LinuxBoot(machine.Machine):
    _linux_init_event: typing.Optional[tbot.log.EventIO] = None

    def _linux_boot_event(self) -> tbot.log.EventIO:
        if self._linux_init_event is None:
            self._linux_init_event = tbot.log.EventIO(
                ["board", "linux", self.name],
                tbot.log.c("LINUX").bold + f" ({self.name})",
                verbosity=tbot.log.Verbosity.QUIET,
            )

            self._linux_init_event.prefix = "   <> "
            self._linux_init_event.verbosity = tbot.log.Verbosity.STDOUT

        return self._linux_init_event


class LinuxBootLogin(machine.Initializer, LinuxBoot):

    login_prompt = "login: "
    """Prompt that indicates tbot should send the username."""

    login_delay = 0
    """The delay between first occurence of login_prompt and actual login."""

    @property
    @abc.abstractmethod
    def username(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def password(self) -> typing.Optional[str]:
        pass

    @contextlib.contextmanager
    def _init_machine(self) -> typing.Iterator:
        with self._linux_boot_event() as ev, self.ch.with_stream(ev):
            self.ch.read_until_prompt(prompt=self.login_prompt)

            # On purpose do not login immediately as we may get some
            # console flooding from upper SW layers (and tbot's console
            # setup may get broken)
            if self.login_delay != 0:
                try:
                    self.ch.read(timeout=self.login_delay)
                except TimeoutError:
                    pass
                self.ch.sendline("")
                self.ch.read_until_prompt(prompt=self.login_prompt)

            self.ch.sendline(self.username)
            if self.password is not None:
                self.ch.read_until_prompt(prompt="assword: ")
                self.ch.sendline(self.password)

        yield None


Self = typing.TypeVar("Self", bound="LinuxUbootConnector")


class LinuxUbootConnector(connector.Connector, LinuxBootLogin):
    def do_boot(self, ub: board.UBootShell) -> channel.Channel:
        return ub.boot("boot")

    @property
    @abc.abstractmethod
    def uboot(self) -> typing.Type[board.UBootShell]:
        raise NotImplementedError("abstract method")

    def __init__(self, b: typing.Union[board.Board, board.UBootShell]) -> None:
        self._b = b

    @contextlib.contextmanager
    def _connect(self) -> typing.Iterator[channel.Channel]:
        with contextlib.ExitStack() as cx:
            if isinstance(self._b, board.Board):
                ub = cx.enter_context(self.uboot(self._b))  # type: ignore
            elif isinstance(self._b, board.UBootShell):
                ub = cx.enter_context(self._b)
            else:
                raise TypeError(f"Got {self._b!r} instead of Board/U-Boot machine")

            self._linux_boot_event()

            yield self.do_boot(ub).take()

    def clone(self: Self) -> Self:
        raise NotImplementedError("can't clone Linux_U-Boot Machine")
