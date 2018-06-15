"""
Localhost lab config
"""
import pathlib
import getpass
from tbot.config import Config


# pylint: disable=line-too-long
def config(cfg: Config) -> None:
    """ Lab config """
    username = getpass.getuser()
    home = pathlib.Path.home()
    cfg["lab"] = {
        "name": "local",
        "hostname": "localhost",
        "user": username,
        "keyfile": home / ".ssh" / "id_rsa",
    }

    cfg["tbot"] = {"workdir": pathlib.PurePosixPath(home) / ".tbot-workdir"}

    cfg["tftp"] = {
        "root": pathlib.PurePosixPath("/tmp/tftp"),
        "tbotsubdir": pathlib.PurePosixPath("tbot"),
    }

    cfg["uboot"] = {"repository": "git://git.denx.de/u-boot.git", "test.use_venv": True}

    # Change this to your sdk location
    sdk_base_path = pathlib.Path.home() / "Documents" / "sdk"
    sdk_armv7a_hf = {
        "path": sdk_base_path
        / "sysroots/x86_64-pokysdk-linux"
        / "usr"
        / "bin"
        / "arm-poky-linux-gnueabi",
        "env_setup_script": sdk_base_path
        / "environment-setup-cortexa8hf-neon-poky-linux-gnueabi",
        "prefix": "arm-poky-linux-gnueabi-",
    }
    cfg["build"] = {
        "default": "local",
        "local": {
            "username": username,
            "hostname": "localhost",
            "workdir": cfg["tbot.workdir"] / "build",
            "toolchains": {
                "cortexa8hf-neon": sdk_armv7a_hf,
                "generic-armv7a-hf": sdk_armv7a_hf,
            },
        },
    }
