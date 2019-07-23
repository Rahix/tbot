import abc
import typing
from .. import shell
from .special import Special

Self = typing.TypeVar("Self", bound="LinuxShell")
ArgTypes = typing.Union[str, Special[Self]]


class LinuxShell(shell.Shell):
    @abc.abstractmethod
    def exec(self: Self, *args: ArgTypes) -> typing.Tuple[int, str]:
        raise NotImplementedError("abstract method")

    @abc.abstractmethod
    def exec0(self: Self, *args: ArgTypes) -> str:
        raise NotImplementedError("abstract method")

    @abc.abstractmethod
    def test(self: Self, *args: ArgTypes) -> bool:
        raise NotImplementedError("abstract method")

    @abc.abstractmethod
    def env(self: Self, var: str, value: typing.Optional[ArgTypes] = None) -> str:
        raise NotImplementedError("abstract method")

    @abc.abstractmethod
    def interactive(self) -> None:
        raise NotImplementedError("abstract method")
