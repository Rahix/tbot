import abc
import typing
from . import linux_shell  # noqa: F401

H = typing.TypeVar("H", bound="linux_shell.LinuxShell")


class Special(typing.Generic[H]):
    __slots__ = ()

    @abc.abstractmethod
    def _to_string(self, host: H) -> str:
        raise NotImplementedError("abstract method")


class _Static(Special):
    __slots__ = ("string",)

    def __init__(self, string: str) -> None:
        self.string = string

    def _to_string(self, _: H) -> str:
        return self.string


AndThen = _Static("&&")
Background = _Static("&")
OrElse = _Static("||")
Pipe = _Static("|")
Then = _Static(";")
