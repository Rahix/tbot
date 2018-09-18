import typing
import contextlib
import tbot
from tbot.machine import linux


class MiniSSHMachine(linux.SSHMachine):
    hostname = "localhost"
    name = "minissh-local"

    @property
    def username(self) -> str:
        return self._username

    @property
    def port(self) -> int:
        return self._port

    @property
    def workdir(self) -> "linux.Path[MiniSSHMachine]":
        return linux.Workdir.static(self, "/tmp/tbot-wd/minisshd-remote")

    def __init__(self, labhost: linux.LabHost, port: int) -> None:
        self._port = port
        self._username = labhost.username

        super().__init__(labhost)


@tbot.testcase
def check_minisshd(h: linux.LabHost) -> bool:
    """Check if this host can run a minisshd."""
    return h.exec("which", "dropbear")[0] == 0


@tbot.testcase
@contextlib.contextmanager
def minisshd(h: linux.LabHost, port: int = 2022) -> typing.Generator:
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
        h.exec0("kill", pid)
