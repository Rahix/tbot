# tbot, Embedded Automation Tool
# Copyright (C) 2019  Harald Seiler
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

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
    RedirBoth,
    Then,
)
from .workdir import Workdir
from . import build
from .bash import Bash
from .ash import Ash
from .build import Builder
from .lab import Lab
from .util import RunCommandProxy, CommandEndedException
from . import auth

__all__ = (
    "Ash",
    "auth",
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
    "RedirBoth",
    "Then",
    "Workdir",
    "RunCommandProxy",
    "CommandEndedException",
)


#        Compatibility aliases
#        =====================
#        Make migration easier by only warning on use of deprecated items where
#        possible.  For items which cannot be 'emulated', show a comprehensive
#        error message.
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
