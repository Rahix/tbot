import typing
import pathlib

from .linux_shell import LinuxShell
from .bash import Bash
from .special import AndThen, Background, OrElse, Pipe, RedirStderr, RedirStdout, Then

__all__ = (
    "AndThen",
    "Background",
    "Bash",
    "LinuxShell",
    "OrElse",
    "Pipe",
    "RedirStderr",
    "RedirStdout",
    "Then",
)

#        Compatibility aliases
#        =====================

LinuxMachine = LinuxShell
LabHost = LinuxShell
SSHMachine = NotImplementedError

ANY = typing.TypeVar("ANY")


class Path(pathlib.Path, typing.Generic[ANY]):
    def __init__(self) -> None:
        raise NotImplementedError


class build:
    class BuildMachine:
        def __init__(self) -> None:
            raise NotImplementedError

    Toolchain = NotImplementedError


BuildMachine = build.BuildMachine


class lab:
    SSHLabHost = NotImplementedError
    LocalLabHost = NotImplementedError


class shell:
    Bash = NotImplementedError


class auth:
    Authenticator = NotImplementedError
