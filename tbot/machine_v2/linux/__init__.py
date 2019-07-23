from .linux_shell import LinuxShell
from .bash import Bash
from .special import AndThen, Background, OrElse, Pipe, RedirStderr, RedirStdout, Then

LinuxMachine = LinuxShell

__all__ = (
    "AndThen",
    "Background",
    "Bash",
    "LinuxMachine",
    "LinuxShell",
    "OrElse",
    "Pipe",
    "RedirStderr",
    "RedirStdout",
    "Then",
)
