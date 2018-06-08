"""
Corvus (at91sam9g45) board config

Available in ``denx`` and ``local`` labs
"""
import pathlib
from tbot.config import Config


# pylint: disable=line-too-long
def config(cfg: Config) -> None:
    """ Board config """
    if cfg["lab.name"] not in ["pollux", "local"]:
        raise Exception("board corvus: Only pollux and local labs are supported!")

    cfg["board"] = {
        "name": "at91sam9g45",
        "toolchain": "generic-armv7a-hf",
        "power": {
            "on_command": "remote_power at91sam9g45 on",
            "off_command": "remote_power at91sam9g45 off",
        }
        if cfg["lab.name"] == "pollux"
        else {
            "on_command": "echo POWER ON; echo ON >/tmp/powerstate",
            "off_command": "echo POWER_OFF; echo OFF >/tmp/powerstate",
        },
        "serial": {"name": "connect_at91sam9g45", "command": "connect at91sam9g45"}
        if cfg["lab.name"] == "pollux"
        else {
            "name": "local-ub",
            # Fake connect. Also contains a read call to simulate autoboot abort
            "command": "sh\nPROMPT_COMMAND=\nPS1='U-Boot> ';sleep 0.1;echo 'Autoboot: ';read dummyvar",
        },
    }

    cfg["uboot"] = (
        {
            "defconfig": "corvus_defconfig",
            "patchdir": pathlib.PurePosixPath("/home/hws/corvus_patches"),
            "test": {
                "hooks": pathlib.PurePosixPath("/home/hws/hooks/corvus"),
                "boardname": "corvus",
            },
            "shell": {"prompt": "U-Boot> "},
        }
        if cfg["lab.name"] == "pollux"
        else {
            "defconfig": "corvus_defconfig",
            "patchdir": pathlib.PurePosixPath("/home/hws/Documents/corvus_patches"),
            "env_location": pathlib.PurePosixPath(
                "/home/hws/Documents/tbot2/env/corvus-env.txt"
            ),
            "shell": {
                "autoboot-prompt": r"Autoboot:\s+",
                "prompt": "U-Boot> ",
                "support_echo_e": True,
                "support_printf": True,
                "is_uboot": False,
            },
        }
    )

    cfg["linux"] = (
        {}
        if cfg["lab.name"] == "pollux"
        else {
            "boot_command": """\
sleep 1; \
echo 'Some boot log ...'; \
echo 'Very interesting ...'; \
read -p 'lnx-login: ' dummyvar; read -p 'pw: ' dummyvar; sh""",
            "shell": {
                "username": "root",
                "password": "root",
                "login_prompt": "lnx-login: ",
                "login_timeout": 1,
            },
        }
    )

    cfg["tftp"] = {
        "boarddir": pathlib.PurePosixPath(
            "at91sam9g45" if cfg["lab.name"] == "pollux" else "corvus-local"
        )
    }
