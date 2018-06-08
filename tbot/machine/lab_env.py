"""
Labhost machine with environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
"""
import random
import typing
import paramiko
import tbot
from . import machine
from . import shell_utils


class MachineLabEnv(machine.Machine):
    """ Labhost machine with environment """

    def __init__(self, prompt: typing.Optional[str] = None) -> None:
        self.channel: typing.Optional[paramiko.Channel] = None

        # Set custom prompt to know when output ends
        self.prompt = f"TBOT-{random.randint(100000, 999999)}>"
        if isinstance(prompt, str):
            self.prompt = prompt

        super().__init__()

    def _setup(
        self, tb: "tbot.TBot", previous: typing.Optional[machine.Machine] = None
    ) -> "MachineLabEnv":
        conn = tb.machines.connection
        self.channel = conn.get_transport().open_session()

        shell_utils.setup_channel(self.channel, self.prompt)

        super()._setup(tb, previous)
        return self

    def _exec(
        self, command: str, stdout_handler: typing.Optional[tbot.log.LogStdoutHandler]
    ) -> typing.Tuple[int, str]:
        return shell_utils.command_and_retval(
            self.channel, self.prompt, command, stdout_handler
        )

    @property
    def common_machine_name(self) -> str:
        """ Common name of this machine, always ``"host"`` """
        return "host"

    @property
    def unique_machine_name(self) -> str:
        """ Unique name of this machine, always ``"labhost-env"`` """
        return "labhost-env"
