import abc
import typing
import pathlib
from tbot.machine import linux
from tbot.machine import channel


class LabHost(linux.LinuxMachine):
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"

    # Override exec and exec0 so the signatures are typechecked
    def exec(
        self,
        *args: "typing.Union[str, linux.Path[LabHost]]",
        stdout: "typing.Optional[linux.Path[LabHost]]" = None,
    ) -> typing.Tuple[int, str]:
        return super().exec(*args, stdout=stdout)

    def exec0(
        self,
        *args: "typing.Union[str, linux.Path[LabHost]]",
        stdout: "typing.Optional[linux.Path[LabHost]]" = None,
    ) -> str:
        return super().exec0(*args, stdout=stdout)
