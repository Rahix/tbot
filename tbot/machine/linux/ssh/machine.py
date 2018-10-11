import time
import abc
import pathlib
from tbot import log_event
from tbot.machine import channel
from tbot.machine import linux
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

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} {self.username}@{self.hostname}:{self.port} (Lab: {self.labhost!r}>"
        )

    def _connect(self) -> channel.Channel:
        chan = self.labhost.new_channel()

        hk_disable = ["-o", "StrictHostKeyChecking=no"] if self.ignore_hostkey else []

        authenticator = self.authenticator
        if isinstance(authenticator, auth.PasswordAuthenticator):
            # Careful, password WILL BE LEAKED!
            cmd = ["sshpass", "-p", authenticator.password, "ssh"]
        elif isinstance(authenticator, auth.PrivateKeyAuthenticator):
            cmd = ["ssh", "-o", "BatchMode=yes", "-i", str(authenticator.key)]
        else:
            raise RuntimeError(f"{authenticator!r} is not supported for SSH hosts!")

        cmd_str = self.build_command(
            *cmd, *hk_disable, "-p", str(self.port), f"{self.username}@{self.hostname}"
        )

        with log_event.command(self.labhost.name, cmd_str):
            chan.send(cmd_str + "; exit\n")

        time.sleep(0.5)

        # Reinitialize channel after ssh connection is established

        chan.initialize()

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
