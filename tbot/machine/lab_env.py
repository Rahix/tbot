"""
Labhost machine with environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
"""
import random
import typing
import socket
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

    def _setup(self,
               tb: 'tbot.TBot',
               previous: typing.Optional[machine.Machine] = None,
              ) -> 'MachineLabEnv':
        conn = tb.machines.connection
        self.channel = conn.get_transport().open_session()

        shell_utils.setup_channel(self.channel, self.prompt)

        super()._setup(tb, previous)
        return self

    def _command(self,
                 command: str,
                 log_event: tbot.logger.LogEvent) -> str:
        if not isinstance(self.channel, paramiko.Channel):
            raise Exception("Channel not initialized")

        self.channel.send(f"{command}\n")
        try:
            # Read until next occurence of the prompt. Then cut of the first part,
            # which is the command with a newline, and the last part, which is the
            # prompt for the next command
            stdout = shell_utils.read_to_prompt(
                self.channel,
                self.prompt,
                log_event)[len(command)+1:-len(self.prompt)]
        except socket.timeout:
            # TODO: Better exception handling
            stdout = ""

        return stdout

    def _exec(self,
              command: str,
              log_event: tbot.logger.LogEvent) -> typing.Tuple[int, str]:
        stdout = self._command(command, log_event)

        # Get the return code
        retcode = int(self._command("echo $?", None).strip())

        return retcode, stdout

    @property
    def common_machine_name(self) -> str:
        """ Common name of this machine, always ``"labhost"`` """
        return "labhost"

    @property
    def unique_machine_name(self) -> str:
        """ Unique name of this machine, always ``"labhost-env"`` """
        return "labhost-env"
