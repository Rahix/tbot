import abc
import contextlib
import time
import typing
from .. import machine


class LinuxBootLogin(machine.Initializer):
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
        try:
            print("--> wait for login")
            time.sleep(0.5)
            self.ch.read()
            self.ch.read_until_prompt(prompt="login: ")
            self.ch.sendline(self.username)
            time.sleep(2.0)
            if self.password is not None:
                self.ch.sendline(self.password)
                time.sleep(1.0)
            yield None
        finally:
            pass
