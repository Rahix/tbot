import abc
import typing
from .. import shell, channel
from . import path, workdir
from .special import Special

Self = typing.TypeVar("Self", bound="LinuxShell")


class LinuxShell(shell.Shell):
    @abc.abstractmethod
    def escape(
        self: Self, *args: typing.Union[str, Special[Self], path.Path[Self]]
    ) -> str:
        raise NotImplementedError("abstract method")

    @abc.abstractmethod
    def exec(
        self: Self, *args: typing.Union[str, Special[Self], path.Path[Self]]
    ) -> typing.Tuple[int, str]:
        raise NotImplementedError("abstract method")

    @abc.abstractmethod
    def exec0(
        self: Self, *args: typing.Union[str, Special[Self], path.Path[Self]]
    ) -> str:
        raise NotImplementedError("abstract method")

    @abc.abstractmethod
    def test(
        self: Self, *args: typing.Union[str, Special[Self], path.Path[Self]]
    ) -> bool:
        raise NotImplementedError("abstract method")

    @abc.abstractmethod
    def env(
        self: Self, var: str, value: typing.Union[str, path.Path[Self], None] = None
    ) -> str:
        raise NotImplementedError("abstract method")

    @abc.abstractmethod
    def open_channel(
        self: Self, *args: typing.Union[str, Special[Self], path.Path[Self]]
    ) -> channel.Channel:
        raise NotImplementedError("abstract method")

    @abc.abstractmethod
    def interactive(self) -> None:
        raise NotImplementedError("abstract method")

    @abc.abstractmethod
    def subshell(self: Self) -> typing.ContextManager[Self]:
        pass

    @property
    def username(self) -> str:
        return self.env("USER")

    @property
    def fsroot(self: Self) -> path.Path[Self]:
        return path.Path(self, "/")

    @property
    def workdir(self: Self) -> path.Path[Self]:
        return workdir.Workdir.static(self, "/tmp/tbot-wd")
