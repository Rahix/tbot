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


class Authenticator(abc.ABC):
    """Authenticate a connection to a linux host."""

    pass


class PasswordAuthenticator(Authenticator):
    """Authenticate using a password."""

    __slots__ = ("password",)

    def __init__(self, password: str) -> None:
        """
        Initialize this authenticator with a given password.

        :param str password: The password that will be used
                             with this authenticator.
        """
        self.password = password


class PrivateKeyAuthenticator(Authenticator):
    """Authenticate using a private key."""

    __slots__ = ("key_file",)

    def __init__(self, key_file: pathlib.PurePath) -> None:
        """
        Initialize this authenticator with a path to a private key.

        :param pathlib.Path key_file: Path to the private key file
        """
        self.key_file = key_file
