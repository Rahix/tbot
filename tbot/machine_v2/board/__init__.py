import typing

from .board import PowerControl
from .linux import LinuxBootLogin

__all__ = ("PowerControl", "LinuxBootLogin")

#        Compatibility aliases
#        =====================


class Board:
    def __init__(*args) -> None:
        raise NotImplementedError


ANY = typing.TypeVar("ANY")


class UBootMachine(typing.Generic[ANY]):
    def __init__(*args) -> None:
        raise NotImplementedError


class LinuxWithUBootMachine(typing.Generic[ANY]):
    def __init__(*args) -> None:
        raise NotImplementedError


class LinuxStandaloneMachine(typing.Generic[ANY]):
    def __init__(*args) -> None:
        raise NotImplementedError


from ..linux.special import *  # noqa
