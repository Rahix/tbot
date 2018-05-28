"""
Buildhost machine
^^^^^^^^^^^^^^^^^
"""
import random
import time
import typing
import paramiko
import tbot
from . import machine
from . import shell_utils


class MachineBuild(machine.Machine):
    """ Buildhost machine """

    def __init__(
        self,
        *,
        name: typing.Optional[str] = None,
        username: typing.Optional[str] = None,
        password: typing.Optional[str] = None,
        hostname: typing.Optional[str] = None,
        ssh_command: typing.Optional[str] = None,
    ) -> None:
        super().__init__()
        self.name = name or "default"
        self.prompt = f"TBOT-{random.randint(100000, 999999)}>"

        self.username = username
        self.password = password
        self.hostname = hostname
        self.ssh_command = ssh_command

        self.channel: typing.Optional[paramiko.Channel] = None

    def _setup(
        self, tb: "tbot.TBot", previous: typing.Optional[machine.Machine] = None
    ) -> "MachineBuild":
        if (
            previous is not self
            and isinstance(previous, MachineBuild)
            and previous.unique_machine_name == self.unique_machine_name
        ):
            return previous

        super()._setup(tb, previous)

        if self.name == "default":
            self.name = tb.config["build.default"]
        bhcfg = f"build.{self.name}."

        self.ssh_command = self.ssh_command or tb.config[bhcfg + "ssh_command", None]

        if self.ssh_command is None:
            self.username = self.username or tb.config[bhcfg + "username"]
            self.password = self.password or tb.config[bhcfg + "password", None]
            self.hostname = self.hostname or tb.config[bhcfg + "hostname"]

            self.ssh_command = f"ssh {self.username}@{self.hostname}"

        try:
            prompt = f"TBOT-{random.randint(100000, 999999)}>"
            conn = tb.machines.connection
            self.channel = conn.get_transport().open_session()

            shell_utils.setup_channel(self.channel, prompt)

            self.channel.send(f"{self.ssh_command}\n")

            time.sleep(2)

            self.channel.send(
                f"""\
__SSH_EXIT_CODE_OPT=$?
PROMPT_COMMAND=
PS1='{self.prompt}'
"""
            )

            shell_utils.read_to_prompt(self.channel, self.prompt)

            output = shell_utils.exec_command(
                self.channel, self.prompt, "echo $__SSH_EXIT_CODE_OPT", None
            )
            if int(output) != 0:
                raise Exception("Failed to connect to buildhost")
        except:  # noqa: E722
            raise

        return self

    def _exec(
        self, command: str, stdout_handler: typing.Optional[tbot.log.LogStdoutHandler]
    ) -> typing.Tuple[int, str]:
        stdout = shell_utils.exec_command(
            self.channel, self.prompt, command, stdout_handler
        )

        # Get the return code
        retcode = int(
            shell_utils.exec_command(self.channel, self.prompt, "echo $?", None).strip()
        )

        return retcode, stdout

    @property
    def common_machine_name(self) -> str:
        """ Common name of this machine, always ``"buildhost"`` """
        return "buildhost"

    @property
    def unique_machine_name(self) -> str:
        """ Unique name of this machine, ``"buildhost-<name>"`` """
        return f"buildhost-{self.name}"
