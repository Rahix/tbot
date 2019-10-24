import abc
import contextlib
import typing

import tbot
from . import connector
from .. import linux, channel
from ..linux import auth


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
        if host is not None:
            self.host = host
        else:
            self.host = tbot.acquire_local()  # type: ignore

    @contextlib.contextmanager
    def _connect(self) -> typing.Iterator[channel.Channel]:
        with self.host.clone() as h:
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

            cmd_str = h.escape(
                *cmd,
                *hk_disable,
                *["-p", str(self.port)],
                *[arg for opt in self.ssh_config for arg in ["-o", opt]],
                f"{self.username}@{self.hostname}",
            )

            with tbot.log_event.command(h.name, cmd_str):
                h.ch.sendline(cmd_str + "; exit", read_back=True)

            yield h.ch.take()

    def clone(self) -> "SSHConnector":
        """
        .. todo::

            Make this machine cloneable at some point.
        """
        raise NotImplementedError("can't clone an ssh connection")
