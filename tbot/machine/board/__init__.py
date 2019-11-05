import typing

from .uboot import UBootShell, UBootAutobootIntercept
from .board import PowerControl, Board, Connector
from .linux import LinuxUbootConnector, LinuxBootLogin
from ..linux.special import Then, AndThen, OrElse, Raw

__all__ = (
    "AndThen",
    "Board",
    "Connector",
    "LinuxUbootConnector",
    "LinuxBootLogin",
    "OrElse",
    "PowerControl",
    "Raw",
    "Then",
    "UBootAutobootIntercept",
    "UBootMachine",
    "UBootShell",
)

#        Compatibility aliases
#        =====================

ANY = typing.TypeVar("ANY")


class UBootMachine(typing.Generic[ANY], UBootShell):
    # Old UBootMachine had a generic parameter.  This wrapper is necessary to
    # "emulate" that fake generic.
    pass


class LinuxWithUBootMachine(typing.Generic[ANY]):
    def __init__(*args) -> None:
        raise NotImplementedError


class LinuxStandaloneMachine(typing.Generic[ANY]):
    def __init__(*args) -> None:
        raise NotImplementedError
