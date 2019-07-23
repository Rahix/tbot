import abc
import getpass
import paramiko
import pathlib
import typing

import tbot
from .. import channel
from . import connector

Self = typing.TypeVar("Self", bound="ParamikoConnector")


class ParamikoConnector(connector.Connector):
    __slots__ = ("_client", "_config")

    @property
    @abc.abstractmethod
    def hostname(self) -> str:
        """
        Return the hostname of this lab.

        You must always specify this parameter in your Lab config!
        """
        pass

    @property
    def username(self) -> str:
        """
        Return the username to login as.

        Defaults to the username from ``~/.ssh/config`` or the local username.
        """
        if "user" in self._config:
            assert isinstance(self._config["user"], str)
            return self._config["user"]
        else:
            return getpass.getuser()

    @property
    def port(self) -> int:
        """
        Return the port the remote SSH server is listening on.

        Defaults to ``22`` or the value of ``Port`` in ``~/.ssh/config``.
        """
        if "port" in self._config:
            assert isinstance(self._config["port"], str)
            return int(self._config["port"])
        else:
            return 22

    @property
    def ignore_hostkey(self) -> bool:
        """
        Ignore host key.

        Set this to true if the remote changes its host key often.

        Defaults to ``False`` or the value of ``StrictHostKeyChecking`` in
        ``~/.ssh/config``.
        """
        if "stricthostkeychecking" in self._config:
            assert isinstance(self._config["stricthostkeychecking"], str)
            return self._config["stricthostkeychecking"] == "no"
        else:
            return False

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} {self.username}@{self.hostname}:{self.port}>"
        )

    def __init__(self, other: "typing.Optional[ParamikoConnector]" = None) -> None:
        self._client: typing.Optional[paramiko.SSHClient] = None
        self._config: typing.Dict[str, typing.Union[str, typing.List[str]]] = {}

        if other is not None:
            self._client = other._client
            self._config = other._config

    def _connect(self) -> channel.Channel:
        if self._client is None:
            self._client = paramiko.SSHClient()

            try:
                c = paramiko.config.SSHConfig()
                c.parse(open(pathlib.Path.home() / ".ssh" / "config"))
                self._config = c.lookup(self.hostname)
            except FileNotFoundError:
                # Config file does not exist
                pass
            except Exception:
                # Invalid config
                tbot.log.warning(tbot.log.c("Invalid").red + " .ssh/config")
                raise

            if self.ignore_hostkey:
                self._client.set_missing_host_key_policy(
                    paramiko.client.AutoAddPolicy()
                )
            else:
                self._client.load_system_host_keys()

            tbot.log.message(
                "Logging in on "
                + tbot.log.c(f"{self.username}@{self.hostname}:{self.port}").yellow
                + " ...",
                verbosity=tbot.log.Verbosity.COMMAND,
            )

            if "hostname" in self._config:
                hostname = str(self._config["hostname"])
            else:
                hostname = self.hostname

            self._client.connect(hostname, username=self.username, port=self.port)

        return channel.ParamikoChannel(self._client.get_transport().open_session())

    def clone(self: Self) -> Self:
        return type(self)(self)
