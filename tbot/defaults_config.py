"""
defaults_config.py: Last config to be applied, that
sets sane defaults where possible
"""
import random
import pathlib
from tbot.config import Config


def config(cfg: Config) -> None:
    """ Default value config """
    # tbot.workdir: All files that a tbot run produces while running should be stored in
    # some subdir of this path. (Except eg. tftp boot files)
    rand = random.randint(1000, 10000)
    cfg["tbot.workdir"] = cfg[
        "tbot.workdir", pathlib.PurePosixPath(f"/tmp/tbot-{rand}")
    ]

    # uboot.builddir: U-Boot's repository clone, used to build U-Boot
    cfg["uboot.builddir"] = cfg["uboot.builddir", f"uboot-{cfg['board.name']}"]

    if cfg["tftp.boarddir", None] is not None:
        cfg["tftp.directory"] = cfg[
            "tftp.directory", cfg["tftp.boarddir"] / cfg["tftp.tbotsubdir", "tbot"]
        ]
