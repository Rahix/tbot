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
import pathlib
import getpass
import typing

from paramiko import ssh_exception, pkey, rsakey, dsskey, ecdsakey, ed25519key


class Authenticator(abc.ABC):
    """Authenticate a connection to a linux host."""

    def __init__(
        self,
        password: typing.Optional[str] = None,
        key_file: typing.Optional[pathlib.PurePath] = None,
        key: typing.Optional[pkey.PKey] = None,
    ):
        """
        Initializes this authenticator with the given parameters.

        :param str password: Password
        :param str key_file: Privat key file path.
        :param any key: Privat key object
        """
        self.password = password
        self.key_file = key_file
        self.key = key


class PasswordAuthenticator(Authenticator):
    """Authenticate using a password."""

    def __init__(self, password: str) -> None:
        """
        Initialize this authenticator with a given password.

        :param str password: The password that will be used
                             with this authenticator.
        """
        super().__init__(password=password)
        self.password: str


class PrivateKeyAuthenticator(Authenticator):
    """Authenticate using a private key."""

    def __init__(self, key: pathlib.PurePath) -> None:
        """
        Initialize this authenticator with a path to a private key.

        :param pathlib.Path key: Path to the private key file
        """
        super().__init__(key_file=key)
        self.key_file: pathlib.PurePath

        for key_type in (
            rsakey.RSAKey,
            dsskey.DSSKey,
            ecdsakey.ECDSAKey,
            ed25519key.Ed25519Key,
        ):
            for count in range(4):
                try:
                    self.key = key_type.from_private_key_file(
                        filename=str(self.key_file), password=self.password
                    )
                    return
                except ssh_exception.PasswordRequiredException:
                    if count == 3:
                        raise
                    self.password = getpass.getpass(
                        f"Enter passphrase for key '{self.key_file}': "
                    )
                except ssh_exception.SSHException:
                    break

        raise ssh_exception.SSHException(f"Unable to use key file '{self.key_file}'")


class NoneAuthenticator(Authenticator):
    """
    Authenticates without key or password.
    Useful if an ssh-agent is running in the background on LabHosts.
    """

    def __init__(self) -> None:
        """Initialize this authenticator."""
        super().__init__()
        self.password: None
        self.key: None
        self.key_file: None
