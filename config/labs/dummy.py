import re
import getpass
from tbot.machine.linux import lab
from tbot.machine import linux


def get_sshd_port() -> int:
    try:
        with open("/etc/ssh/sshd_config") as f:
            s = f.read()
            m = re.search(r"^Port\s+(?P<port>\d+)", s, re.M)
            if m is None:
                return 22
            return int(m.group("port"))
    except PermissionError or IOError:
        return 22


class DummyLab(lab.LabHost):
    name = "local"
    hostname = "localhost"
    port = get_sshd_port()
    username = getpass.getuser()

    @property
    def workdir(self) -> "linux.path.Path[DummyLab]":
        p = linux.path.Path(self, "/tmp/tbot-dir")
        self.exec0("mkdir", "-p", p)
        return p
