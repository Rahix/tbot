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

import typing
import tbot
from tbot.machine import linux, connector
from tbot.machine.linux import auth

__all__ = ("copy",)

H1 = typing.TypeVar("H1", bound=linux.LinuxMachine)
H2 = typing.TypeVar("H2", bound=linux.LinuxMachine)


def _scp_copy(
    *,
    local_path: linux.Path[H1],
    remote_path: linux.Path[H2],
    copy_to_remote: bool,
    username: str,
    hostname: str,
    ignore_hostkey: bool,
    port: int,
    ssh_config: typing.List[str],
    authenticator: auth.Authenticator,
) -> None:
    local_host = local_path.host

    hk_disable = ["-o", "StrictHostKeyChecking=no"] if ignore_hostkey else []

    scp_command = [
        "scp",
        *["-P", str(port)],
        *hk_disable,
        *[arg for opt in ssh_config for arg in ["-o", opt]],
    ]

    if isinstance(authenticator, auth.PrivateKeyAuthenticator):
        scp_command += ["-o", "BatchMode=yes", "-i", authenticator.key_file]
    elif isinstance(authenticator, auth.NoneAuthenticator):
        scp_command += ["-o", "BatchMode=yes"]
    elif isinstance(authenticator, auth.PasswordAuthenticator):
        scp_command = ["sshpass", "-p", authenticator.password] + scp_command

    if copy_to_remote:
        local_host.exec0(
            *scp_command,
            local_path,
            f"{username}@{hostname}:{remote_path._local_str()}",
        )
    else:
        local_host.exec0(
            *scp_command,
            f"{username}@{hostname}:{remote_path._local_str()}",
            local_path,
        )


@tbot.testcase
def copy(p1: linux.Path[H1], p2: linux.Path[H2]) -> None:
    """
    Copy a file, possibly from one host to another.

    The following transfers are currently supported:

    * ``H`` 🢥 ``H`` (transfer without changing host)
    * **lab-host** 🢥 **ssh-machine** (:py:class:`~tbot.machine.connector.SSHConnector`, using ``scp``)
    * **ssh-machine** 🢥 **lab-host** (Using ``scp``)
    * **local-host** 🢥 **paramiko-host** (:py:class:`~tbot.machine.connector.ParamikoConnector`, using ``scp``)
    * **paramiko-host** 🢥 **local-host** (Using ``scp``)

    The following transfers are **not** supported:

    * **ssh-machine** 🢥 **ssh-machine** (There is no guarantee that two remote hosts can
      connect to each other.  If you need this, transfer to the lab-host first
      and then to the other remote)
    * **lab-host** 🢥 **board-machine** (Transfers over serial are not (yet) implemented.
      To 'upload' files, connect to your target via ssh or use a tftp download)

    :param linux.Path p1: Exisiting path to be copied
    :param linux.Path p2: Target where ``p1`` should be copied
    """
    if isinstance(p1.host, p2.host.__class__) or isinstance(p2.host, p1.host.__class__):
        # Both paths are on the same host
        p2_w1 = linux.Path(p1.host, p2)
        p1.host.exec0("cp", p1, p2_w1)
        return
    elif isinstance(p1.host, connector.SSHConnector) and p1.host.host is p2.host:
        # Copy from an SSH machine
        _scp_copy(
            local_path=p2,
            remote_path=p1,
            copy_to_remote=False,
            username=p1.host.username,
            hostname=p1.host.hostname,
            ignore_hostkey=p1.host.ignore_hostkey,
            port=p1.host.port,
            ssh_config=p1.host.ssh_config,
            authenticator=p1.host.authenticator,
        )
    elif isinstance(p2.host, connector.SSHConnector) and p2.host.host is p1.host:
        # Copy to an SSH machine
        _scp_copy(
            local_path=p1,
            remote_path=p2,
            copy_to_remote=True,
            username=p2.host.username,
            hostname=p2.host.hostname,
            ignore_hostkey=p2.host.ignore_hostkey,
            port=p2.host.port,
            ssh_config=p2.host.ssh_config,
            authenticator=p2.host.authenticator,
        )
    elif isinstance(p1.host, connector.SubprocessConnector) and isinstance(
        p2.host, connector.ParamikoConnector
    ):
        # Copy from local to ssh labhost
        _scp_copy(
            local_path=p1,
            remote_path=p2,
            copy_to_remote=True,
            username=p2.host.username,
            hostname=p2.host.hostname,
            ignore_hostkey=p2.host.ignore_hostkey,
            port=p2.host.port,
            ssh_config=[],
            authenticator=p2.host.authenticator,
        )
    elif isinstance(p2.host, connector.SubprocessConnector) and isinstance(
        p1.host, connector.ParamikoConnector
    ):
        # Copy to local from ssh labhost
        _scp_copy(
            local_path=p2,
            remote_path=p1,
            copy_to_remote=False,
            username=p1.host.username,
            hostname=p1.host.hostname,
            ignore_hostkey=p1.host.ignore_hostkey,
            port=p1.host.port,
            ssh_config=[],
            authenticator=p1.host.authenticator,
        )
    else:
        raise NotImplementedError(f"Can't copy from {p1.host} to {p2.host}!")
