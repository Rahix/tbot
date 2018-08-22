import typing
import getpass
from tbot.machine import linux
from tbot.machine import channel
from . import lab

LLH = typing.TypeVar("LLH", bound="LocalLabHost")


class LocalLabHost(lab.LabHost):
    name = "local"

    @property
    def workdir(self) -> "linux.Path[LocalLabHost]":
        p = linux.Path(self, "/tmp/tbot-wd")
        self.exec0("mkdir", "-p", p)
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
