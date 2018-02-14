import pathlib
from tbot.config import Config

#pylint: disable=line-too-long
def config(cfg: Config) -> None:
    if cfg["lab.name"] not in ["pollux", "local"]:
        raise Exception("board corvus: Only pollux and local labs are supported!")

    cfg["board"] = {
        "name": "at91sam9g45",
        "toolchain": "cortexa8hf-neon",
        "defconfig": "corvus_defconfig",
        "power": {
            "on_command": "remote_power at91sam9g45 on",
            "off_command": "remote_power at91sam9g45 off",
        } if cfg["lab.name"] == "pollux" else {
            "on_command": "echo POWER ON; echo ON >/tmp/powerstate",
            "off_command": "echo POWER_OFF; echo OFF >/tmp/powerstate",
        },
        "shell": {
            "name": "connect_at91sam9g45",
            "command": "connect at91sam9g45",
            "prompt": "U-Boot> ",
        } if cfg["lab.name"] == "pollux" else {
            "name": "local-ub",
            # Fake connect. Also contains a read call to simulate autoboot abort
            "command": "sh\nPROMPT_COMMAND=\nPS1='U-Boot> ';read",
            "prompt": "U-Boot> ",
            "timeout": 0.1,
            "support_echo_e": True,
            "support_printf": True,
            "is_uboot": False,
        },
    }

    cfg["uboot"] = {
        "patchdir": pathlib.PurePosixPath("/home/hws/corvus_patches"),
        "test": {
            "hooks": pathlib.PurePosixPath("/home/hws/hooks/corvus"),
            "boardname": "corvus",
        },
    } if cfg["lab.name"] == "pollux" else {
        "patchdir": pathlib.PurePosixPath("/home/hws/Documents/corvus_patches"),
        "env_location": pathlib.PurePosixPath("/home/hws/Documents/tbot2/env/corvus-env.txt"),
    }

    cfg["tftp"] = {
        "boarddir": pathlib.PurePosixPath("at91sam9g45" if cfg["lab.name"] == "pollux" else "corvus-local"),
    }
