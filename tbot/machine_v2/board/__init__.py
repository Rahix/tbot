import typing

from .uboot import UBootShell, UBootAutobootIntercept
from .board import PowerControl
from .linux import LinuxBootLogin

__all__ = (
    "LinuxBootLogin",
    "PowerControl",
    "UBootAutobootIntercept",
    "UBootMachine",
    "UBootShell",
)

#        Compatibility aliases
#        =====================

ANY = typing.TypeVar("ANY")


class UBootMachine(typing.Generic[ANY], UBootShell):
    pass


class Board:
    def __init__(*args) -> None:
        raise NotImplementedError


class LinuxWithUBootMachine(typing.Generic[ANY]):
    def __init__(*args) -> None:
        raise NotImplementedError


class LinuxStandaloneMachine(typing.Generic[ANY]):
    def __init__(*args) -> None:
        raise NotImplementedError


from ..linux.special import *  # noqa
