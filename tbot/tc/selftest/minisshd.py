import getpass
import typing
import contextlib
import tbot
from tbot.machine import linux


class MiniSSHMachine(linux.SSHMachine):
    """SSHMachine for test purposes."""

    hostname = "localhost"
    name = "minissh-local"
    ignore_hostkey = True

    @property
    def username(self) -> str:
        """Return local username."""
        return self._username

    @property
    def port(self) -> int:
        """Return local ssh server port."""
        return self._port

    @property
    def workdir(self) -> "linux.Path[MiniSSHMachine]":
        """Return a workdir."""
        return linux.Workdir.static(self, "/tmp/tbot-wd/minisshd-remote")

    def __init__(self, labhost: linux.LabHost, port: int) -> None:
        """Create a new MiniSSHMachine."""
        self._port = port
        self._username = labhost.username

        super().__init__(labhost)


class MiniSSHLabHost(linux.lab.SSHLabHost):
    """SSHLabHost for test purposes."""

    hostname = "localhost"
    name = "minissh-lab"
    ignore_hostkey = True

    @property
    def username(self) -> str:
        """Return local username."""
        return self._username

    @property
    def port(self) -> int:
        """Return local ssh server port."""
        return self._port

    @property
    def workdir(self) -> "linux.Path[MiniSSHLabHost]":
        """Return a workdir."""
        return linux.Workdir.static(self, "/tmp/tbot-wd/minisshd-remote")

    def __init__(self, port: int) -> None:
        """Create a new MiniSSHMachine."""
        self._port = port
        self._username = getpass.getuser()

        super().__init__()


@tbot.testcase
def check_minisshd(h: linux.LabHost) -> bool:
    """Check if this host can run a minisshd."""
    return h.test("which", "dropbear")


@tbot.testcase
@contextlib.contextmanager
def minisshd(h: linux.LabHost, port: int = 2022) -> typing.Generator:
    """
    Create a new minisshd server and machine.

    Intended for use in a ``with``-statement::

        if check_minisshd(lh):
            with minisshd(lh) as ssh:
                ssh.exec0("uname", "-a")

    :param linux.LabHost h: lab-host
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

    pid = h.exec0("cat", pid_file).strip()

    try:
        ssh_machine = MiniSSHMachine(h, port)
        yield ssh_machine
    finally:
        tbot.log.message("Stopping dropbear ...")
        h.exec0("kill", pid)
