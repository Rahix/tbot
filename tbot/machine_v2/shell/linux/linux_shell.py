import abc
import typing
from ... import shell


class LinuxShell(shell.Shell):
    @abc.abstractmethod
    def exec(self, *args: str) -> typing.Tuple[int, str]:
        raise NotImplementedError("abstract method")

    @abc.abstractmethod
    def exec0(self, *args: str) -> str:
        raise NotImplementedError("abstract method")
