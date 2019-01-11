# tbot, Embedded Automation Tool
# Copyright (C) 2018  Harald Seiler
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import abc
import typing
import pathlib
from tbot import log_event
from tbot.machine import channel, linux
from tbot.machine.linux import auth


class SSHMachine(linux.LinuxMachine):
    """Generic machine that can be reached via SSH from the LabHost."""

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
        return self.labhost.username

    @property
    def authenticator(self) -> auth.Authenticator:
        """
        Return an authenticator that allows logging in on this machine.

        .. danger::
            It is strongly advised to use key authentication.  If you use password
            auth, **THE PASSWORD WILL BE LEAKED** and **MIGHT EASILY BE STOLEN**
            by other users on your labhost.  It will also be visible in the log file.

            If you decide to use this, you're doing this on your own risk.

            The only case where I support using passwords is when connecting to
            a test board with a default password.

        :rtype: tbot.machine.linux.auth.Authenticator
        """
        return auth.PrivateKeyAuthenticator(pathlib.Path.home() / ".ssh" / "id_rsa")

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

            class MySSHMach(linux.SSHMachine):
                ssh_config = ["ProxyJump=foo@example.com"]

        :rtype: list(str)

        .. versionadded:: 0.6.2
        """
        return []

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.username}@{self.hostname}:{self.port} (Lab: {self.labhost!r}>"

    def _connect(self) -> channel.Channel:
        chan = self.labhost.new_channel()

        hk_disable = ["-o", "StrictHostKeyChecking=no"] if self.ignore_hostkey else []

        authenticator = self.authenticator
        if isinstance(authenticator, auth.PasswordAuthenticator):
            # Careful, password WILL BE LEAKED!
            cmd = ["sshpass", "-p", authenticator.password, "ssh"]
        elif isinstance(authenticator, auth.PrivateKeyAuthenticator):
            cmd = ["ssh", "-o", "BatchMode=yes", "-i", str(authenticator.key_file)]
        elif isinstance(authenticator, auth.NoneAuthenticator):
            cmd = ["ssh", "-o", "BatchMode=yes"]
        else:
            raise RuntimeError(f"{authenticator!r} is not supported for SSH hosts!")

        cmd_str = self.build_command(
            *cmd,
            *hk_disable,
            *["-p", str(self.port)],
            *[arg for opt in self.ssh_config for arg in ["-o", opt]],
            f"{self.username}@{self.hostname}",
        )

        try:
            with log_event.command(self.labhost.name, cmd_str) as ev:
                send_str = cmd_str + "; exit\n"
                chan.send(send_str)
                # Read back command
                chan.recv_n(len(send_str) + 1)

                head = b""
                try:
                    while True:
                        head += chan.recv(timeout=0.1)
                except TimeoutError:
                    pass
                finally:
                    try:
                        ev.write(head.decode("utf-8"))
                    except UnicodeDecodeError:
                        ev.write(head.decode("latin1"))

            # Reinitialize channel after ssh connection is established
            chan.initialize()
        except channel.ChannelClosedException:
            raise RuntimeError("SSH connection failed: Remote closed port")

        return chan

    def __init__(self, labhost: linux.LabHost) -> None:
        """
        Connect to this SSH machine.

        :param tbot.machine.linux.LabHost labhost: LabHost from where to attempt connecting
        """
        super().__init__()
        self.labhost = labhost

        self.channel = self._connect()

    def _obtain_channel(self) -> channel.Channel:
        return self.channel

    def destroy(self) -> None:
        """Destory this SSHMachine instance."""
        self.channel.close()

    @property
    def lh(self) -> linux.LabHost:
        """Return the lab-host that was used to establish this machines connection."""
        return self.labhost
