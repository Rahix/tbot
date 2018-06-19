"""
Dummy Board Config
"""
from tbot.config import Config


def config(cfg: Config) -> None:
    """ Board config """

    cfg["board"] = {
        "name": "dummy-board",
        "toolchain": "dummy",
        "power": {
            "on_command": "echo POWER ON; echo ON >/tmp/powerstate",
            "off_command": "echo POWER_OFF; echo OFF >/tmp/powerstate",
        },
        "serial": {
            "name": "local-ub",
            # Fake connect. Also contains a read call to simulate autoboot abort
            "command": "sh\nPROMPT_COMMAND=\nPS1='U-Boot> ';sleep 0.1;echo 'Autoboot: ';read dummyvar",
        },
    }

    cfg["uboot"] = {
        "shell": {
            "autoboot-prompt": r"Autoboot:\s+",
            "prompt": "U-Boot> ",
            "support_echo_e": True,
            "support_printf": True,
            "is_uboot": False,
        }
    }

    cfg["linux"] = {
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
