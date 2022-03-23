# tbot, Embedded Automation Tool
# Copyright (C) 2019  Harald Seiler
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
import contextlib
import typing

import tbot
from . import connector
from .. import linux, channel
from ..linux import auth

Self = typing.TypeVar("Self", bound="SSHConnector")


class SSHConnector(connector.Connector):
    """
    Connect to remote using ``ssh`` by starting off from an existing machine.

    An :py:class:`SSHConnector` is different from a
    :py:class:`ParamikoConnector` as it requires an existing machine to start
    the connection from.  This allows jumping via one host to a second.

    **Example**:

    .. code-block:: python

        import tbot
        from tbot.machine import connector, linux

        # Connect into a container running on the (possibly remote) lab-host
        class MyRemote(
            connector.SSHConnector,
            linux.Bash,
        ):
            hostname = "localhost"
            port = 20220
            username = "root"

        with tbot.acquire_lab() as lh:
            # lh might be a ParamikoConnector machine.
            with MyRemote(lh) as ssh_session:
                ssh_session.exec0("uptime")
    """

    @property
    def ignore_hostkey(self) -> bool:
        """
        Ignore host key.

        Set this to true if the remote changes its host key often.
        """
        return False

    @property
    def use_multiplexing(self) -> bool:
        """
        Whether tbot should attempt to enable connection multiplexing.

        Connection multiplexing is a mechanism to share a connection between
        multiple sessions.  This can drastically speed up your tests when many
        connections to the same machine are opened and closed.  Refer to
        `ControlMaster in sshd_config(5)`_ for details.

        .. _ControlMaster in sshd_config(5): https://man.openbsd.org/ssh_config.5#ControlMaster

        .. versionadded:: 0.9.0
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
    def authenticator(self) -> auth.Authenticator:
        """
        Return an authenticator that allows logging in on this machine.

        See :mod:`tbot.machine.linux.auth` for available authenticators.

        .. danger::
            It is strongly advised to use key authentication.  If you use password
            auth, **THE PASSWORD WILL BE LEAKED** and **MIGHT EASILY BE STOLEN**
            by other users on your labhost.  It will also be visible in the log file.

            If you decide to use this, you're doing this on your own risk.

            The only case where I support using passwords is when connecting to
            a test board with a default password.

        :rtype: tbot.machine.linux.auth.Authenticator
        """
        return auth.NoneAuthenticator()

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

    def __init__(self, host: typing.Optional[linux.LinuxShell] = None) -> None:
        self.host: linux.LinuxShell
        self.host = host  # type: ignore

    @classmethod
    @contextlib.contextmanager
    def from_context(
        cls: typing.Type[Self], ctx: "tbot.Context"
    ) -> typing.Iterator[Self]:
        with contextlib.ExitStack() as cx:
            lh = None
            if isinstance(cls, ctx.get_machine_class(tbot.role.LabHost)):
                lh = cx.enter_context(ctx.request(tbot.role.LabHost))
            m = cx.enter_context(cls(lh))  # type: ignore
            yield typing.cast(Self, m)

    @contextlib.contextmanager
    def _connect(self) -> typing.Iterator[channel.Channel]:
        with contextlib.ExitStack() as cx:
            if self.host is None:
                self.host = cx.enter_context(tbot.acquire_local())
            h = cx.enter_context(self.host.clone())

            authenticator = self.authenticator
            if isinstance(authenticator, auth.NoneAuthenticator):
                cmd = ["ssh", "-o", "BatchMode=yes"]
            elif isinstance(authenticator, auth.PrivateKeyAuthenticator):
                cmd = [
                    "ssh",
                    "-o",
                    "BatchMode=yes",
                    "-i",
                    authenticator.get_key_for_host(h),
                ]
            elif isinstance(authenticator, auth.PasswordAuthenticator):
                cmd = ["sshpass", "-p", authenticator.password, "ssh"]
            else:
                if typing.TYPE_CHECKING:
                    authenticator._undefined_marker
                raise ValueError(f"Unknown authenticator {authenticator!r}")

            hk_disable = (
                ["-o", "StrictHostKeyChecking=no"] if self.ignore_hostkey else []
            )

            multiplexing = []
            if self.use_multiplexing:
                multiplexing_dir = self.host.workdir / ".ssh-multi"
                self.host.exec0("mkdir", "-p", multiplexing_dir)

                multiplexing += ["-o", "ControlMaster=auto"]
                multiplexing += ["-o", "ControlPersist=10m"]
                multiplexing += [
                    "-o",
                    f"ControlPath={multiplexing_dir.at_host(self.host)}/%C",
                ]

            cmd_str = h.escape(
                *cmd,
                *hk_disable,
                *multiplexing,
                *["-p", str(self.port)],
                *[arg for opt in self.ssh_config for arg in ["-o", opt]],
                f"{self.username}@{self.hostname}",
            )

            with tbot.log_event.command(h.name, cmd_str):
                h.ch.sendline(cmd_str + "; exit", read_back=True)

            yield h.ch.take()

    def clone(self) -> "SSHConnector":
        """Clone this machine."""
        new = type(self)(self.host)
        new._orig = self._orig or self
        return new
