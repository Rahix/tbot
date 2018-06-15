"""
Buildhost machine
^^^^^^^^^^^^^^^^^
"""
import random
import time
import typing
import pathlib
import socket
import paramiko
import tbot
from . import machine
from . import shell_utils


class MachineBuild(machine.Machine):
    """
    Buildhost machine

    :param str name: Name of the buildhost, as found in the config. Defaults to
                     the value of ``tb.config["build.default"]``
    :param str username: Username on the buildhost, defaults to
                         ``tb.config["build.<name>.username"]``
    :param str password: Password on the buildhost, if passwordless login is not
                         available, defaults to
                         ``tb.config["build.<name>.password"]``

                         .. todo:: Not implemented yet, you have to use\
                            passwordless login
    :param str hostname: Hostname of the buildhost, defaults to
                         ``tb.config["build.<name>.hostname"]``
    :param str ssh_command: If this parameter is not given, TBot will use
                            ``ssh <username>@<hostname>``. If it is given,
                            it will be used instead. This allows for custom
                            ssh options like using a different key.
    """

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
        self._workdir = None

        self.username = username
        self.password = password
        # TODO: Actually use the password
        self.hostname = hostname
        self.ssh_command = ssh_command

        self.channel: typing.Optional[paramiko.Channel] = None

    def _setup(
        self, tb: "tbot.TBot", previous: typing.Optional[machine.Machine] = None
    ) -> "MachineBuild":
        if self.name == "default":
            self.name = tb.config["build.default"]

        if (
            previous is not self
            and isinstance(previous, MachineBuild)
            and previous.unique_machine_name == self.unique_machine_name
        ):
            return previous

        super()._setup(tb, previous)

        bhcfg = f"build.{self.name}."
        self._workdir = tb.config[bhcfg + "workdir", None]

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

            self.channel.send(f"{self.ssh_command}; exit\n")

            time.sleep(2)

            self.channel.send(
                f"""\
PROMPT_COMMAND=
PS1='{self.prompt}'
"""
            )

            shell_utils.read_to_prompt(self.channel, self.prompt)
        except socket.error:
            raise Exception("SSH connection to buildhost failed")
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
    def workdir(self) -> pathlib.PurePosixPath:
        if self._workdir is None:
            raise Exception("No workdir specified for this buildhost")
        return self._workdir

    @property
    def common_machine_name(self) -> str:
        """ Common name of this machine, always ``"host"`` """
        return "host"

    @property
    def unique_machine_name(self) -> str:
        """ Unique name of this machine, ``"buildhost-<name>"`` """
        return f"buildhost-{self.name}"
