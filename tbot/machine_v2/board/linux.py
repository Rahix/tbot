import abc
import contextlib
import typing
import tbot
from .. import machine


class LinuxBootLogin(machine.Initializer):

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
        with tbot.log.EventIO(
            ["board", "linux", self.name],
            tbot.log.c("LINUX").bold + f" ({self.name})",
            verbosity=tbot.log.Verbosity.QUIET,
        ) as ev, self.ch.with_stream(ev):
            ev.prefix = "   <> "
            ev.verbosity = tbot.log.Verbosity.STDOUT

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
