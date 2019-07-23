import abc
import typing
from .. import shell
from . import path
from .special import Special

Self = typing.TypeVar("Self", bound="LinuxShell")
ArgTypes = typing.Union[str, Special[Self], path.Path[Self]]


class LinuxShell(shell.Shell):
    __slots__ = ("_workdir",)

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

    @abc.abstractmethod
    def subshell(self: Self) -> typing.ContextManager[Self]:
        pass

    @property
    def fsroot(self: Self) -> path.Path[Self]:
        return path.Path(self, "/")

    @property
    def workdir(self: Self) -> path.Path[Self]:
        try:
            return self._workdir
        except AttributeError:
            self._workdir: path.Path[Self] = path.Path(self, "/tmp/tbot-wd")
            self.exec0("mkdir", "-p", self._workdir)
            return self._workdir
