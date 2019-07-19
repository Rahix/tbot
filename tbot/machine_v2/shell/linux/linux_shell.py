import abc
import typing
from ... import shell
from .special import Special

ArgTypes = typing.Union[str, Special]


class LinuxShell(shell.Shell):
    @abc.abstractmethod
    def exec(self, *args: ArgTypes) -> typing.Tuple[int, str]:
        raise NotImplementedError("abstract method")

    @abc.abstractmethod
    def exec0(self, *args: ArgTypes) -> str:
        raise NotImplementedError("abstract method")

    @abc.abstractmethod
    def test(self, *args: ArgTypes) -> bool:
        raise NotImplementedError("abstract method")
