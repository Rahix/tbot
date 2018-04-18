"""
Buildhost machine
^^^^^^^^^^^^^^^^^
"""
import random
import typing
import paramiko
import tbot
from . import machine
from . import shell_utils

class MachineBuild(machine.Machine):
    """ Buildhost machine """
    def __init__(self, name: typing.Optional[str] = None) -> None:
        self.name = name or "unkwon"
        self.prompt = f"TBOT-{random.randint(100000, 999999)}>"

    def _exec(self,
              command: str,
              log_event: tbot.logger.LogEvent) -> typing.Tuple[int, str]:
        raise Exception("Unimplemented!")

    @property
    def common_machine_name(self) -> str:
        """ Common name of this machine, always ``"buildhost"`` """
        return "buildhost"

    @property
    def unique_machine_name(self) -> str:
        """ Unique name of this machine, ``"buildhost-<name>"`` """
        return f"buildhost-{self.name}"
