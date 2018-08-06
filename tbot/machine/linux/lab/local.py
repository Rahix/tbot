import typing
import getpass
from tbot.machine import linux  # noqa: F401
from tbot.machine import channel
from . import lab

LLH = typing.TypeVar("LLH", bound="LocalLabHost")


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

    def new_channel(self) -> channel.Channel:
        return channel.SubprocessChannel()

    # Override exec and exec0 so the signatures are typechecked
    def exec(
        self,
        *args: "typing.Union[str, linux.Path[LLH]]",
        stdout: "typing.Optional[linux.Path[LLH]]" = None,
    ) -> typing.Tuple[int, str]:
        return super().exec(*args, stdout=stdout)

    def exec0(
        self,
        *args: "typing.Union[str, linux.Path[LLH]]",
        stdout: "typing.Optional[linux.Path[LLH]]" = None,
    ) -> str:
        return super().exec0(*args, stdout=stdout)
