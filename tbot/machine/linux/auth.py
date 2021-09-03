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

import typing
import pathlib
from .. import linux


class AuthenticatorBase:
    pass


class PasswordAuthenticator(AuthenticatorBase):
    """
    Authenticate using a password.

    .. danger::

        This method is very insecure and might lead to **PASSWORDS BEING STOLEN**.


    **Example**:

    .. code-block:: python

        class MySSHHost(connector.SSHConnector, linux.Bash):
            username = "root"
            authenticator = linux.auth.PasswordAuthenticator("hunter2")
    """

    __slots__ = ("password",)

    def __init__(self, password: str) -> None:
        self.password = password


class PrivateKeyAuthenticator(AuthenticatorBase):
    """
    Authenticate using a private-key file.

    **Example**:

    .. code-block:: python

        class MySSHHost(connector.SSHConnector, linux.Bash):
            username = "foouser"
            authenticator = linux.auth.PrivateKeyAuthenticator("/home/foo/.ssh/id_rsa_foo")
    """

    __slots__ = ("key_file",)

    def __init__(
        self, key_file: typing.Union[str, linux.Path, pathlib.PurePath]
    ) -> None:
        self.key_file = key_file

    def get_key_for_host(self, host: typing.Optional[linux.LinuxShell]) -> str:
        if isinstance(self.key_file, str):
            return self.key_file
        elif isinstance(self.key_file, pathlib.PurePath):
            return str(self.key_file)
        elif isinstance(self.key_file, linux.Path):
            if host is None:
                return self.key_file.at_host(self.key_file.host)
            return self.key_file.at_host(host)
        else:
            raise TypeError(f"`host` has wrong type for get_key_for_host()")


class NoneAuthenticator(AuthenticatorBase):
    """
    Most primitive authenticator.

    Tries not passing any specific credentials and hopes ssh-config already
    contains all necessary infos.  This is the default.
    """

    pass


class UndefinedAuthenticator(AuthenticatorBase):
    # Python has no real union types which could be used to ensure all variants
    # are checked in code.  As a workaround, the else-branch should access this
    # _undefined_marker property like this:
    #
    #     else:
    #         if typing.TYPE_CHECKING:
    #             authenticator._undefined_marker
    #         raise ValueError(f"Unknown authenticator {authenticator!r}")
    #
    # mypy will then raise an error if any variants were not checked in
    # elif-blocks beforehand.
    _undefined_marker = None


Authenticator = typing.Union[
    PasswordAuthenticator,
    PrivateKeyAuthenticator,
    NoneAuthenticator,
    UndefinedAuthenticator,
]
