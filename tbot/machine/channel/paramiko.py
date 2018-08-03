import paramiko
from tbot.machine import channel


class ParamikoChannel(channel.Channel):
    def __init__(self, ch: paramiko.Channel) -> None:
        self.ch = ch

    def close(self) -> None:
        self.ch.close()
