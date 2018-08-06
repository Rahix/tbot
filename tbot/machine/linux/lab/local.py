import getpass
from tbot.machine import channel
from . import lab


class LocalLabHost(lab.LabHost):
    @property
    def username(self) -> str:
        return getpass.getuser()

    def __init__(self) -> None:
        self.channel = channel.SubprocessChannel()

    def destroy(self) -> None:
        self.channel.close()

    def _obtain_channel(self) -> channel.Channel:
        return self.channel
