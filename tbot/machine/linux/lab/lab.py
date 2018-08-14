import abc
import typing
from tbot.machine import linux
from tbot.machine import channel


class LabHost(linux.LinuxMachine):

    @abc.abstractmethod
    def new_channel(self) -> channel.Channel:
        """
        Create a new channel for use by another machine.

        :rtype: channel.Channel
        :returns: A new channel to this lab host
        """
        pass

    @property
    def default_build(self) -> typing.Type[linux.BuildMachine]:
        raise KeyError("No default build machine available!")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"
