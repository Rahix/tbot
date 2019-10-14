import typing

from .linux_shell import LinuxShell
from .path import Path
from .special import (
    AndThen,
    Background,
    OrElse,
    Pipe,
    Raw,
    RedirStderr,
    RedirStdout,
    Then,
)
from .workdir import Workdir
from . import build
from .bash import Bash
from .ash import Ash
from .build import Builder
from .lab import Lab

__all__ = (
    "Ash",
    "build",
    "AndThen",
    "Background",
    "Bash",
    "Builder",
    "Lab",
    "LinuxShell",
    "OrElse",
    "Path",
    "Pipe",
    "Raw",
    "RedirStderr",
    "RedirStdout",
    "Then",
    "Workdir",
)

#        Compatibility aliases
#        =====================

LinuxMachine = LinuxShell
LabHost = Lab
SSHMachine = NotImplementedError

ANY = typing.TypeVar("ANY")


class lab:
    SSHLabHost = NotImplementedError
    LocalLabHost = NotImplementedError


class shell:
    Bash = NotImplementedError


class auth:
    class Authenticator:
        pass

    PrivateKeyAuthenticator = NotImplementedError
    PasswordAuthenticator = NotImplementedError
    NoneAuthenticator = NotImplementedError
