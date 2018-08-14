from tbot.machine.linux import lab
from tbot.machine import linux


class PolluxLab(lab.SSHLabHost):
    name = "pollux"
    hostname = "pollux.denx.de"
    username = "hws"

    @property
    def workdir(self) -> "linux.path.Path[PolluxLab]":
        p = linux.path.Path(self, "/work/hws/tbot-tmp")
        self.exec0("mkdir", "-p", p)
        return p


LAB = PolluxLab
