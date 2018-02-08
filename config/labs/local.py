from tbot.config import Config

#pylint: disable=line-too-long
def config(cfg: Config) -> None:
    cfg["lab"] = {
        "name": "local",
        "hostname": "localhost",
        "user": "hws",
        "keyfile": "/home/hws/.ssh/id_rsa",
    }

    cfg["tbot"] = {
        "workdir": "/home/hws/tbotdir",
    }

    cfg["tftp"] = {
        "rootdir": "/tmp/tftp",
        "tbotsubdir": "tbot",
    }

    cfg["uboot"] = {
        "repository": "git://git.denx.de/u-boot.git",
        "test_use_venv": True,
    }

    cfg["toolchains.cortexa8hf-neon"] = {
        "path": "/home/hws/Documents/sdk/sysroots/x86_64-pokysdk-linux/usr/bin/arm-poky-linux-gnueabi",
        "env_setup_script": "/home/hws/Documents/sdk/environment-setup-cortexa8hf-neon-poky-linux-gnueabi",
        "prefix": "arm-poky-linux-gnueabi-",
    }
