import abc
import shlex
import typing

from . import linux_shell, path  # noqa: F401

H = typing.TypeVar("H", bound="linux_shell.LinuxShell")


class Special(typing.Generic[H]):
    __slots__ = ()

    @abc.abstractmethod
    def _to_string(self, host: H) -> str:
        raise NotImplementedError("abstract method")


class Raw(Special[H]):
    __slots__ = ("string",)

    def __init__(self, string: str) -> None:
        self.string = string

    def _to_string(self, _: H) -> str:
        return self.string


class _Stdio(Special[H]):
    __slots__ = ("file",)

    @property
    @abc.abstractmethod
    def _redir_token(self) -> str:
        raise NotImplementedError("abstract method")

    def __init__(self, file: path.Path[H]) -> None:
        self.file = file

    def _to_string(self, h: H) -> str:
        if self.file.host is not h:
            raise Exception("wrong host")
        return self._redir_token + shlex.quote(self.file._local_str())


class RedirStdout(_Stdio[H]):
    _redir_token = ">"


class RedirStderr(_Stdio[H]):
    _redir_token = "2>"


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
