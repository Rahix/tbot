import abc
import typing
import tbot
from tbot.machine import linux
from tbot.machine import channel
from tbot.machine.linux import special

Self = typing.TypeVar("Self", bound="LabHost")


class LabHost(linux.LinuxMachine):

    @abc.abstractmethod
    def _new_channel(self) -> channel.Channel:
        pass

    def new_channel(
        self: Self, *args: typing.Union[str, special.Special, linux.Path[Self]]
    ) -> channel.Channel:
        chan = self._new_channel()
        if args != ():
            cmd = self.build_command(*args)
            tbot.log.command(self.name, cmd)
            chan.send(cmd + "\n")
            # Read back the command we just sent
            chan.recv()
        return chan

    @property
    def default_build(self) -> typing.Type[linux.BuildMachine]:
        raise KeyError("No default build machine available!")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"
