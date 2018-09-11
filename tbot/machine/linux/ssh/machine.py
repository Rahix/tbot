import time
import abc
import pathlib
from tbot.machine import channel
from tbot.machine import linux
from tbot.machine.linux import auth


class SSHMachine(linux.LinuxMachine):

    @property
    @abc.abstractmethod
    def hostname(self) -> str:
        """Return the hostname of this machine."""
        pass

    @property
    def authenticator(self) -> auth.Authenticator:
        """Return an authenticator that allows logging in on this machine."""
        return auth.PrivateKeyAuthenticator(pathlib.Path.home() / ".ssh" / "id_rsa")

    @property
    def port(self) -> int:
        """Return the port the SSH server is listening on."""
        return 22

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} {self.username}@{self.hostname}:{self.port} (Lab: {self.labhost!r}>"
        )

    def connect(self) -> channel.Channel:
        chan = self.labhost.new_channel()

        authenticator = self.authenticator
        if isinstance(authenticator, auth.PasswordAuthenticator):
            raise RuntimeError("Password authentication is not yet supported")
        if not isinstance(authenticator, auth.PrivateKeyAuthenticator):
            raise RuntimeError("Only key authentication is supported")

        chan.send(
            f"ssh -o BatchMode=yes -i {authenticator.key} {self.username}@{self.hostname}; exit\n"
        )

        time.sleep(0.5)

        # Reinitialize channel after ssh connection is established

        chan.initialize()

        return chan

    def __init__(self, labhost: linux.LabHost) -> None:
        super().__init__()
        self.labhost = labhost

        self.channel = self.connect()

    def _obtain_channel(self) -> channel.Channel:
        return self.channel

    def destroy(self) -> None:
        self.channel.close()
