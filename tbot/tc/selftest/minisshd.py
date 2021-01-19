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

import getpass
import typing
import contextlib
import tbot
from tbot.machine import linux, connector


class MiniSSHMachine(connector.SSHConnector, linux.Bash):
    """SSHMachine for test purposes."""

    hostname = "localhost"
    name = "minissh-local"
    # This would work as well, but we need to test ssh_config somewhere ...
    # ignore_hostkey = True
    ssh_config = ["StrictHostKeyChecking=no"]

    @property
    def username(self) -> str:
        return self._username

    @property
    def port(self) -> int:
        return self._port

    @property
    def workdir(self) -> "linux.Path[MiniSSHMachine]":
        """Return a workdir."""
        return linux.Workdir.static(self, "/tmp/tbot-wd/minisshd-remote")

    def __init__(self, labhost: linux.Lab, port: int) -> None:
        """Create a new MiniSSHMachine."""
        self._port = port
        self._username = labhost.env("USER")

        super().__init__(labhost)


class MiniSSHLabHostBase(linux.Bash):
    name = "minissh-lab"

    @property
    def hostname(self) -> str:
        return "localhost"

    @property
    def ignore_hostkey(self) -> bool:
        return True

    @property
    def username(self) -> str:
        return self._username

    @property
    def port(self) -> int:
        return self._port

    @property
    def workdir(self) -> linux.Path:
        """Return a workdir."""
        return linux.Workdir.static(self, "/tmp/tbot-wd/minisshd-remote")

    def __init__(self, port: int) -> None:
        """Create a new MiniSSHMachine."""
        self._port = port
        self._username = getpass.getuser()

        super().__init__()


if hasattr(connector, "ParamikoConnector"):

    class MiniSSHLabHostParamiko(MiniSSHLabHostBase, connector.ParamikoConnector):
        name = "minissh-lab-paramiko"

    has_paramiko = True
else:
    has_paramiko = False


class MiniSSHLabHostSSH(MiniSSHLabHostBase, connector.SSHConnector):
    name = "minissh-lab-ssh"


@tbot.testcase
def check_minisshd(h: linux.Lab) -> bool:
    """Check if this host can run a minisshd."""
    return h.test("which", "dropbear")


@tbot.testcase
@contextlib.contextmanager
def minisshd(h: linux.Lab, port: int = 2022) -> typing.Generator:
    """
    Create a new minisshd server and machine.

    Intended for use in a ``with``-statement::

        if check_minisshd(lh):
            with minisshd(lh) as ssh:
                ssh.exec0("uname", "-a")

    :param linux.Lab h: lab-host
    :param int port: Port for the ssh server, defaults to ``2022``.
    :rtype: MiniSSHMachine
    """
    server_dir = h.workdir / "minisshd"
    h.exec0("mkdir", "-p", server_dir)

    key_file = server_dir / "ssh_host_key"
    pid_file = server_dir / "dropbear.pid"

    # Create host key
    if not key_file.exists():
        h.exec0("dropbearkey", "-t", "rsa", "-f", key_file)

    h.exec0("dropbear", "-p", "127.0.0.1:2022", "-r", key_file, "-P", pid_file)

    # Try reading the file again if it does not yet exist
    for i in range(10):
        ret, pid = h.exec("cat", pid_file)
        if ret == 0:
            pid = pid.strip()
            break
    else:
        raise RuntimeError("dropbear did not create a pid-file!")

    try:
        with MiniSSHMachine(h, port) as ssh_machine:
            yield ssh_machine
    finally:
        tbot.log.message("Stopping dropbear ...")
        h.exec0("kill", pid)
