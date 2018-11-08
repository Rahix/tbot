import abc
import typing
import tbot
from tbot.machine import linux
from tbot.machine import channel
from tbot.machine.linux import special

Self = typing.TypeVar("Self", bound="LabHost")


class LabHost(linux.LinuxMachine):
    """Generic LabHost abstraction."""

    @abc.abstractmethod
    def _new_channel(self) -> channel.Channel:
        pass

    def new_channel(
        self: Self, *args: typing.Union[str, special.Special, linux.Path[Self]]
    ) -> channel.Channel:
        """
        Create a new channel for a new machine instance via this LabHost.

        If ``*args`` is non-empty, it is interpreted as a command that will be
        run on the LabHost to open a connection to the new machine. Once this
        command finished, the new channel will be closed.

        If ``*args`` is empty, a shell on the LabHost is opened, that you can
        run commands using eg. :meth:`~tbot.machine.channel.Channel.raw_command`.

        **Example**::

            with tbot.acquire_lab() as lh:
                bdi_ch = lh.new_channel("telnet", "bdi4")

                # Do something with the bdi
        """
        chan = self._new_channel()
        if args != ():
            cmd = self.build_command(*args)
            tbot.log_event.command(self.name, cmd)
            # Send exit after the command so this channel will close once it
            # is done.
            chan.send(cmd + " ; exit\n")
            # Read back the command we just sent
            chan.recv()
        return chan

    @property
    def default_build(self) -> typing.Type[linux.BuildMachine]:
        """
        Return the default buildhost for this lab.

        **Example**::

            with tbot.acquire_lab() as lh:
                with lh.default_build(arch="generic-armv7a") as bh:
                    assert bh.exec0("echo", linux.Env("ARCH") == "arm"
        """
        raise KeyError("No default build machine available!")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"
