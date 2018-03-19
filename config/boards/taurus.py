"""
Taurus board config

Available in ``denx`` lab
"""
import pathlib
from tbot.config import Config

#pylint: disable=line-too-long
def config(cfg: Config) -> None:
    """ Board config """
    if cfg["lab.name"] != "pollux":
        raise Exception("board taurus: Only availabe in pollux lab!")

    cfg["board"] = {
        "name": "at91_taurus",
        "toolchain": "generic-armv7a-hf",
        "power": {
            "on_command": "remote_power at91_taurus on",
            "off_command": "remote_power at91_taurus off",
        },
        "shell": {
            "name": "connect_at91_taurus",
            "command": "connect at91_taurus",
            "prompt": "U-Boot> ",
        },
    }

    cfg["uboot"] = {
        "defconfig": "taurus_defconfig",
        "patchdir": pathlib.PurePosixPath("/work/hs/tbot/patches/taurus_uboot_patches"),
        "env_location": pathlib.PurePosixPath("/home/hws/env/taurus-env.txt"),
    }

    cfg["tftp"] = {
        "boarddir": "at91_taurus",
    }
