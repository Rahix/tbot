import pathlib
import importlib
import random
import typing
from tbot import config



def parse_config(configs: typing.List[pathlib.Path]) -> config.Config:
    cfg = config.Config()
    for cfg_file in configs:
        module_spec = importlib.util.spec_from_file_location("config", str(cfg_file))

        if hasattr(module_spec, "loader") and isinstance(module_spec.loader, importlib.abc.Loader):
            module = importlib.util.module_from_spec(module_spec)
            module_spec.loader.exec_module(module)
        else:
            raise Exception(f"Failed to load {cfg_file}")

        if "config" in module.__dict__:
            module.__dict__["config"](cfg)
        else:
            raise Exception(f"{cfg_file} is not a valid TBot configuration!")

    cfg.workdir = pathlib.PurePosixPath(
        cfg["tbot.workdir",
            f"/tmp/tbot-{cfg['board.name']}-{random.randint(1000, 10000)}"])
    return cfg
