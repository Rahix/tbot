import typing
import getpass
from tbot.machine import linux
from tbot.machine import channel
from .machine import LabHost

LLH = typing.TypeVar("LLH", bound="LocalLabHost")


class LocalLabHost(LabHost):
    name = "local"

    @property
    def workdir(self: LLH) -> "linux.Path[LLH]":
        p = linux.Path(self, "/tmp/tbot-wd")
        # Only create workdir once
        if not hasattr(self, "_wd_marker"):
            if not p.exists():
                self.exec0("mkdir", "-p", p)
            setattr(self, "_wd_marker", None)
        return p

    @property
    def username(self) -> str:
        return getpass.getuser()

    def __init__(self) -> None:
        super().__init__()
        self.channel = channel.SubprocessChannel()

    def destroy(self) -> None:
        self.channel.close()

    def _obtain_channel(self) -> channel.Channel:
        return self.channel

    def _new_channel(self) -> channel.Channel:
        return channel.SubprocessChannel()
