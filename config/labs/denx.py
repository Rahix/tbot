from tbot.config import Config

#pylint: disable=line-too-long
def config(cfg: Config) -> None:
    cfg["lab"] = {
        "name": "pollux",
        "hostname": "pollux.denx.de",
        "user": "hws",
        "keyfile": "/home/hws/.ssh/id_rsa",
    }

    cfg["tbot.workdir"] = "/work/hws/tbot2workdir"

    cfg["tftp"] = {
        "rootdir": "/tftpboot",
        "tbotsubdir": "tbot-hws",
    }

    cfg["uboot"] = {
        "repository": "/home/git/u-boot.git",
        # Pollux does not have venv installed
        "test_use_venv": False,
    }

    cfg["toolchains"] = {
        "cortexa8hf-neon": {
            "path": "/opt/poky/cortexa8hf-neon-2.4.1/sysroots/x86_64-pokysdk-linux/usr/bin/arm-poky-linux-gnueabi",
            "env_setup_script": "/opt/poky/cortexa8hf-neon-2.4.1/environment-setup-cortexa8hf-neon-poky-linux-gnueabi",
            "prefix": "arm-poky-linux-gnueabi-",
        },
        "generic-armv7a-hf": {
            "path": "/opt/yocto-2.4/generic-armv7a-hf/sysroots/x86_64-pokysdk-linux/usr/bin/arm-poky-linux-gnueabi",
            "env_setup_script": "/opt/yocto-2.4/generic-armv7a-hf/environment-setup-armv7ahf-neon-poky-linux-gnueabi",
            "prefix": "arm-poky-linux-gnueabi-",
        },
        "generic-powerpc-e500v2": {
            "path": "/opt/yocto-2.4/generic-powerpc-e500v2/sysroots/x86_64-pokysdk-linux/usr/bin/powerpc-poky-linux-gnuspe",
            "env_setup_script": "/opt/yocto-2.4/generic-powerpc-e500v2/environment-setup-ppce500v2-poky-linux-gnuspe",
            "prefix": "powerpc-poky-linux-gnuspe-",
        },
    }
