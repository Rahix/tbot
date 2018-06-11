"""
DENX pollux lab config
"""
import pathlib
from tbot.config import Config


# pylint: disable=line-too-long
def config(cfg: Config) -> None:
    """ Lab config """
    username = "hws"
    cfg["lab"] = {
        "name": "pollux",
        "hostname": "pollux.denx.de",
        "user": username,
        "keyfile": pathlib.Path.home() / ".ssh" / "id_rsa",
    }

    cfg["tbot.workdir"] = pathlib.PurePosixPath("/work") / username / "tbot-workdir"

    cfg["tftp"] = {
        "root": pathlib.PurePosixPath("/tftpboot"),
        "tbotsubdir": pathlib.PurePosixPath(f"tbot-{username}"),
    }

    cfg["uboot"] = {
        "repository": "/home/git/u-boot.git",
        # Pollux does not have venv installed
        "test.use_venv": False,
    }

    cfg["build"] = {
        "default": "hercules",
        "local": "pollux",
        "pollux": {
            "ssh_command": f"ssh -i ~/.ssh/id_rsa_nopw {username}@localhost",
            "scp_command": f"scp -i ~/.ssh/id_rsa_nopw",
            "scp_address": f"{username}@localhost",
            "workdir": pathlib.PurePosixPath("/work") / username / "tbot-build",
            "toolchains": {
                "cortexa8hf-neon": {
                    "path": pathlib.PurePosixPath(
                        "/opt/poky/cortexa8hf-neon-2.4.1/sysroots/x86_64-pokysdk-linux/usr/bin/arm-poky-linux-gnueabi"
                    ),
                    "env_setup_script": pathlib.PurePosixPath(
                        "/opt/poky/cortexa8hf-neon-2.4.1/environment-setup-cortexa8hf-neon-poky-linux-gnueabi"
                    ),
                    "prefix": "arm-poky-linux-gnueabi-",
                },
                "generic-armv7a-hf": {
                    "path": pathlib.PurePosixPath(
                        "/opt/yocto-2.4/generic-armv7a-hf/sysroots/x86_64-pokysdk-linux/usr/bin/arm-poky-linux-gnueabi"
                    ),
                    "env_setup_script": pathlib.PurePosixPath(
                        "/opt/yocto-2.4/generic-armv7a-hf/environment-setup-armv7ahf-neon-poky-linux-gnueabi"
                    ),
                    "prefix": "arm-poky-linux-gnueabi-",
                },
                "generic-powerpc-e500v2": {
                    "path": pathlib.PurePosixPath(
                        "/opt/yocto-2.4/generic-powerpc-e500v2/sysroots/x86_64-pokysdk-linux/usr/bin/powerpc-poky-linux-gnuspe"
                    ),
                    "env_setup_script": pathlib.PurePosixPath(
                        "/opt/yocto-2.4/generic-powerpc-e500v2/environment-setup-ppce500v2-poky-linux-gnuspe"
                    ),
                    "prefix": "powerpc-poky-linux-gnuspe-",
                },
            },
        },
        "hercules": {
            "ssh_command": f"ssh -i ~/.ssh/id_rsa_nopw {username}@hercules",
            "scp_command": f"scp -i ~/.ssh/id_rsa_nopw",
            "scp_address": f"{username}@hercules",
            "workdir": pathlib.PurePosixPath("/work") / username / "tbot-build",
            "toolchains": {
                "generic-powerpc-e500v2": {
                    "env_setup_script": pathlib.PurePosixPath(
                        "/opt/eldk/build/work/hws/p2020/sdk/environment-setup-ppce500v2-poky-linux-gnuspe"
                    )
                },
                "generic-armv7a-hf": {
                    "env_setup_script": pathlib.PurePosixPath(
                        "/opt/eldk/build/work/hws/lweimx6/sdk2/environment-setup-armv7ahf-neon-poky-linux-gnueabi"
                    )
                },
                "generic-armv7a": {
                    "env_setup_script": pathlib.PurePosixPath(
                        "/opt/eldk/build/work/hws/lweimx6/sdk/environment-setup-armv7a-neon-poky-linux-gnueabi"
                    )
                },
            },
        },
    }
