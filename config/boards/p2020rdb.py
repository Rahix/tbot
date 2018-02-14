"""
P2020RDB-PCA board config

Available in denx lab
"""
import pathlib
from tbot.config import Config

def config(cfg: Config) -> None:
    """ Board config """
    if cfg["lab.name"] != "pollux":
        raise Exception("board p2020rdb: Only availabe in pollux lab!")

    cfg["board"] = {
        "name": "p2020rdb",
        "toolchain": "generic-powerpc-e500v2",
        "defconfig": "P2020RDB-PC_NAND_defconfig",
        "power": {
            "on_command": "remote_power p2020rdb_1 on",
            "off_command": "remote_power p2020rdb_1 off",
        },
        "shell": {
            "name": "connect_p2020rdb_1",
            "command": "connect p2020rdb_1",
            "prompt": "=> ",
        },
    }

    cfg["uboot"] = {
        "test": {
            "hooks": pathlib.PurePosixPath("/home/hws/hooks/P2020"),
            "config": pathlib.PurePosixPath("/home/hws/data/u_boot_boardenv_P2020RDB_PC_NAND.py"),
            "boardname": "P2020RDB-PC_NAND",
        },
    }

    cfg["tftp"] = {
        "boarddir": "p2020rdb",
    }
