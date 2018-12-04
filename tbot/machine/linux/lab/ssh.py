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
import getpass
import pathlib
import paramiko
from tbot.machine import channel
from tbot.machine.linux import auth
from tbot import log
from .machine import LabHost

SLH = typing.TypeVar("SLH", bound="SSHLabHost")


class SSHLabHost(LabHost):
    """
    LabHost that can be connected to via SSH.

    Makes use of :class:`~tbot.machine.channel.ParamikoChannel`.

    To use a LabHost that is connected via SSH, you must subclass
    SSHLabHost in you lab config.

    By default ``SSHLabHost`` tries to get connection info from ``~/.ssh/config``,
    but you can also overwrite this in your config.

    **Example**::

        from tbot.machine.linux import lab
        from tbot.machine import linux


        class MySSHLab(lab.SSHLabHost):
            name = "my-ssh-lab"
            hostname = "lab.example.com"
            username = "admin"

            @property
            def workdir(self) -> "linux.Path[MySSHLab]":
                p = linux.Path(self, "/tmp/tbot-wd")
                self.exec0("mkdir", "-p", p)
                return p


        LAB = MySSHLab
    """

    @property
    def ignore_hostkey(self) -> bool:
        """
        Ignore host key.

        Set this to true if the remote changes its host key often.

        Defaults to ``False`` or the value of ``StrictHostKeyChecking`` in
        ``~/.ssh/config``.
        """
        if "stricthostkeychecking" in self._c:
            assert isinstance(self._c["stricthostkeychecking"], str)
            return self._c["stricthostkeychecking"] == "no"
        else:
            return False

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
        if "user" in self._c:
            assert isinstance(self._c["user"], str)
            return self._c["user"]
        else:
            return getpass.getuser()

    @property
    def authenticator(self) -> auth.Authenticator:
        """
        Return an :class:`~tbot.machine.linux.auth.Authenticator` that allows logging in on this LabHost.

        Defaults to a private key authenticator using ``~/.ssh/id_rsa`` or the first key
        specified in ``~/.ssh/config``.
        """
        if "identityfile" in self._c:
            assert isinstance(self._c["identityfile"], list)
            return auth.PrivateKeyAuthenticator(
                pathlib.Path(self._c["identityfile"][0])
            )

        return auth.PrivateKeyAuthenticator(pathlib.Path.home() / ".ssh" / "id_rsa")

    @property
    def port(self) -> int:
        """
        Return the port the remote SSH server is listening on.

        Defaults to ``22`` or the value of ``Port`` in ``~/.ssh/config``.
        """
        if "port" in self._c:
            assert isinstance(self._c["port"], str)
            return int(self._c["port"])
        else:
            return 22

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} {self.username}@{self.hostname}:{self.port}>"
        )

    def __init__(self) -> None:
        """Create a new instance of this SSH LabHost."""
        super().__init__()
        self.client = paramiko.SSHClient()
        self._c: typing.Dict[str, typing.Union[str, typing.List[str]]] = {}
        try:
            c = paramiko.config.SSHConfig()
            c.parse(open(pathlib.Path.home() / ".ssh" / "config"))
            self._c = c.lookup(self.hostname)
        except FileNotFoundError:
            # Config file does not exist
            pass
        except Exception:
            # Invalid config
            log.message(log.c("Invalid").red + " .ssh/config")
            raise

        if self.ignore_hostkey:
            self.client.set_missing_host_key_policy(paramiko.client.AutoAddPolicy())
        else:
            self.client.load_system_host_keys()

        password = None
        key_file = None

        authenticator = self.authenticator
        if isinstance(authenticator, auth.PasswordAuthenticator):
            password = authenticator.password
        if isinstance(authenticator, auth.PrivateKeyAuthenticator):
            key_file = str(authenticator.key_file)

        log.message(
            "Logging in on "
            + log.c(f"{self.username}@{self.hostname}:{self.port}").yellow
            + " ...",
            verbosity=log.Verbosity.COMMAND,
        )
        self.client.connect(
            self.hostname,
            username=self.username,
            port=self.port,
            password=password,
            key_filename=key_file,
        )

        self.channel = channel.ParamikoChannel(
            self.client.get_transport().open_session()
        )

    def destroy(self) -> None:
        """
        Destroy this LabHost instance.

        .. warning::
            Closes all channels that are still open. You should not call this method
            unless you know what you are doing. The preferred way is to use a context
            block using ``with``.
        """
        self.client.close()

    def _obtain_channel(self) -> channel.Channel:
        return self.channel

    def _new_channel(self) -> channel.Channel:
        return channel.ParamikoChannel(self.client.get_transport().open_session())
