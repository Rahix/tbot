import contextlib
from typing import Iterator, Union

import tbot
from tbot.machine import channel, connector, linux


class Localhost(connector.SubprocessConnector, linux.Bash, tbot.role.Role):
    name = "local"

    @property
    def workdir(self) -> linux.Path:
        return linux.Workdir.xdg_runtime(self, "selftest-data")

    def init(self) -> None:
        self.exec0("rm", "-rf", self.workdir)
        self.exec0("mkdir", self.workdir)


class LocalhostBash(connector.ConsoleConnector, linux.Bash, tbot.role.Role):
    name = "local-bash"

    @property
    def workdir(self) -> linux.Path:
        return linux.Workdir.xdg_runtime(self, "selftest-data-bash")

    def init(self) -> None:
        self.exec0("rm", "-rf", self.workdir)
        self.exec0("mkdir", self.workdir)

    def connect(self, mach: linux.LinuxShell) -> channel.Channel:
        return mach.open_channel("bash", "--norc", "--noprofile")


class LocalhostAsh(connector.ConsoleConnector, linux.Ash, tbot.role.Role):
    name = "local-ash"

    @property
    def workdir(self) -> linux.Path:
        return linux.Workdir.xdg_runtime(self, "selftest-data-ash")

    def init(self) -> None:
        self.exec0("rm", "-rf", self.workdir)
        self.exec0("mkdir", self.workdir)

    @contextlib.contextmanager
    def subshell(
        self, *args: Union[str, linux.special.Special, linux.Path]
    ) -> "Iterator[LocalhostAsh]":
        # Patch the shell invocation command if no args are given because we're
        # not using real `ash` here ...
        if len(args) == 0:
            args = ("bash", "--posix", "--norc", "--noprofile")

        with super().subshell(*args):
            yield self

    def connect(self, mach: linux.LinuxShell) -> channel.Channel:
        # Make sure the terminal is wide enough to not cause breaks.
        mach.exec0("stty", "cols", "1024")
        return mach.open_channel("bash", "--posix", "--norc", "--noprofile")


def register_machines(ctx: tbot.Context) -> None:
    ctx.register(Localhost, [Localhost, tbot.role.LabHost])
    ctx.register(LocalhostBash, [LocalhostBash])
    ctx.register(LocalhostAsh, [LocalhostAsh])
