import typing
import tbot
from tbot.machine import linux

H = typing.TypeVar("H", bound=linux.LinuxMachine)
H2 = typing.TypeVar("H2", bound=linux.LinuxMachine)


@tbot.testcase
def copy(p1: linux.Path[H], p2: linux.Path[H2]) -> None:
    if p1.host is p2.host:
        # Both paths are on the same host
        p1.host.exec0("cp", p1, typing.cast(linux.Path[H], p2))
    else:
        raise NotImplementedError(f"Can't copy from {p1.host} to {p2.host}!")
