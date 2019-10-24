import typing
import tbot

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
#        Make migration easier by only warning on use of deprecated items where
#        possible.  For items which cannot be 'emulated', show a comprehensive
#        error message.


class auth:
    class Authenticator:
        pass

    PrivateKeyAuthenticator = NotImplementedError
    PasswordAuthenticator = NotImplementedError
    NoneAuthenticator = NotImplementedError


def __getattr__(name: str) -> typing.Any:

    from .. import connector

    class DeprecatedSSHMachine(connector.SSHConnector, Bash):
        pass

    deprecated = {
        "LinuxMachine": LinuxShell,
        "LabHost": Lab,
        "SSHMachine": DeprecatedSSHMachine,
        "lab": None,
        "shell": None,
    }

    if name in deprecated:
        tbot.log.warning(
            f"You seem to be using a deprecated item '{__name__}.{name}'.\n"
            + "    Please read the migration guide to learn how to replace it!"
        )
        item = deprecated[name]
        if item is None:
            raise AttributeError(
                f"deprecated item '{__name__}.{name}' is no longer available!"
            )
        return item

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
