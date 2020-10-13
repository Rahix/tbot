import typing
import tbot

from .zephyr import ZephyrShell
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
    "ZephyrMachine",
    "ZephyrShell",
)


#        Compatibility aliases
#        =====================
#        Make migration easier by only warning on use of deprecated items where
#        possible.  For items which cannot be 'emulated', show a comprehensive
#        error message.
def __getattr__(name: str) -> typing.Any:

    from .. import linux

    class UBootMachine(Connector, UBootShell):
        pass

    class LinuxWithUBootMachine(LinuxUbootConnector, LinuxBootLogin, linux.Ash):
        pass

    class LinuxStandaloneMachine(Connector, LinuxBootLogin, linux.Ash):
        pass

    deprecated = {
        "UBootMachine": UBootMachine,
        "LinuxWithUBootMachine": LinuxWithUBootMachine,
        "LinuxStandaloneMachine": LinuxStandaloneMachine,
    }

    if name in deprecated:
        tbot.log.warning(
            f"You seem to be using a deprecated item '{__name__}.{name}'.\n"
            + "    Please read the migration guide to learn how to replace it!"
        )
        item = deprecated[name]
        if item is None:
            raise AttributeError(
                f"deprecated item '{__name__}.{name}' is no longer available!"
            )
        return item

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
