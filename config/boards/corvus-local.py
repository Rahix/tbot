from tbot.config import Config

#pylint: disable=line-too-long
def config(cfg: Config) -> None:
    cfg["board"] = {
        "name": "corvus-local",
        "toolchain": "cortexa8hf-neon",
        "defconfig": "corvus_defconfig",
        "power": {
            "on_command": "echo POWER ON; echo ON >/tmp/powerstate",
            "off_command": "echo POWER_OFF; echo OFF >/tmp/powerstate",
        },
        "shell": {
            "name": "local-ub",
            # Fake connect. Also contains a read call to simulate autoboot abort
            "command": "sh\nPROMPT_COMMAND=\nPS1='U-Boot> ';read",
            "prompt": "U-Boot> ",
            "timeout": 0.1,
            "support_echo_e": True,
            "support_printf": True,
        },
    }

    cfg["uboot"] = {
        "patchdir": "/home/hws/Documents/corvus_patches",
        "env_location": "/home/hws/Documents/tbot2/env/corvus-env.txt",
    }

    cfg["tftp"] = {
        "boarddir": "corvus-local",
    }
