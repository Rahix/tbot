"""
Dummy Lab Config
"""
import re
import pathlib
import getpass
from tbot.config import Config


def get_sshd_port() -> int:
    try:
        with open("/etc/ssh/sshd_config") as f:
            s = f.read()
            m = re.search(r"^Port\s+(?P<port>\d+)", s, re.M)
            if m is None:
                raise Exception("Could not parse port from sshd_config")
            return int(m.group("port"))
    except PermissionError or IOError:
        return 22


def config(cfg: Config) -> None:
    """ Lab config """
    username = getpass.getuser()
    home = pathlib.Path.home()
    sshd_port = get_sshd_port()
    cfg["lab"] = {
        "name": "dummy-lab",
        "hostname": "localhost",
        "port": sshd_port,
        "user": username,
        "keyfile": home / ".ssh" / "id_rsa",
    }

    cfg["tbot"] = {"workdir": pathlib.PurePosixPath(home) / ".tbot-workdir"}

    cfg["tftp"] = {
        "root": pathlib.PurePosixPath("/tmp/tftp"),
        "tbotsubdir": pathlib.PurePosixPath("tbot"),
    }

    cfg["build"] = {
        "default": "local",
        "local": {
            "ssh_command": f"ssh -p {sshd_port} {username}@localhost",
            "scp_command": f"scp -P {sshd_port}",
            "scp_address": f"{username}@localhost",
            "workdir": cfg["tbot.workdir"] / "build",
            "toolchains": {
                "dummy": {
                    "env_setup_script": pathlib.Path(__file__).absolute().parent
                    / "dummy-toolchain.sh"
                }
            },
        },
    }
