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
import typing


class Authenticator(abc.ABC):
    """Authenticate a connection to a linux host."""

    def __init__(
        self,
        password: typing.Optional[str] = None,
        key_file: typing.Optional[pathlib.PurePath] = None,
        key: typing.Optional[typing.Any] = None,
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
