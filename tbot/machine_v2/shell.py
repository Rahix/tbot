import abc
import contextlib
import typing

from . import machine


class Shell(machine.Machine):
    @abc.abstractmethod
    def _init_shell(self) -> typing.ContextManager:
        raise NotImplementedError("abstract method")

    @abc.abstractmethod
    def exec(self, *args: typing.Any) -> typing.Any:
        raise NotImplementedError("abstract method")


class RawShell(machine.Machine):
    @contextlib.contextmanager
    def _init_shell(self) -> typing.Iterator:
        yield None

    def exec(self, *args: str) -> None:
        self.ch.sendline(" ".join(args), read_back=True)

    def interactive(self) -> None:
        self.ch.attach_interactive()
