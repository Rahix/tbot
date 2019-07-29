import abc
import contextlib
import typing

import tbot
from . import connector
from .. import linux, channel


class SSHConnector(connector.Connector):
    @property
    def ignore_hostkey(self) -> bool:
        """
        Ignore host key.

        Set this to true if the remote changes its host key often.
        """
        return False

    @property
    @abc.abstractmethod
    def hostname(self) -> str:
        """
        Return the hostname of this machine.

        :rtype: str
        """
        pass

    @property
    def username(self) -> str:
        """
        Return the username for logging in on this machine.

        Defaults to the username on the labhost.
        """
        return self.host.username

    @property
    def port(self) -> int:
        """
        Return the port the SSH server is listening on.

        :rtype: int
        """
        return 22

    @property
    def ssh_config(self) -> typing.List[str]:
        """
        Add additional ssh config options when connecting.

        **Example**::

            class MySSHMach(connector.SSHConnector, linux.Bash):
                ssh_config = ["ProxyJump=foo@example.com"]

        :rtype: list(str)

        .. versionadded:: 0.6.2
        """
        return []

    def __init__(self, host: linux.LinuxShell) -> None:
        self.host = host

    @contextlib.contextmanager
    def _connect(self) -> typing.Iterator[channel.Channel]:
        with self.host.clone() as h:
            cmd = ["ssh", "-o", "BatchMode=yes"]

            cmd_str = h.escape(
                *cmd,
                *["-p", str(self.port)],
                *[arg for opt in self.ssh_config for arg in ["-o", opt]],
                f"{self.username}@{self.hostname}",
            )

            with tbot.log_event.command(h.name, cmd_str):
                h.ch.sendline(cmd_str + "; exit", read_back=True)

            yield h.ch.take()

    def clone(self) -> "SSHConnector":
        raise NotImplementedError("can't clone an ssh connection")
