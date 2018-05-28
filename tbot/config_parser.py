"""
TBot configuration parser
"""
import pathlib
import importlib
import typing
from tbot import config


def parse_config(cfg: config.Config, configs: typing.List[pathlib.Path]) -> None:
    """
    Parse a list of configurations and apply them in the order they were
    given.

    :param config: Config to apply the files to
    :param configs: List of configuration files
    """
    for cfg_file in configs:
        module_spec = importlib.util.spec_from_file_location(
            cfg_file.stem, str(cfg_file)
        )

        if hasattr(module_spec, "loader") and isinstance(
            module_spec.loader, importlib.abc.Loader
        ):
            module = importlib.util.module_from_spec(module_spec)
            module_spec.loader.exec_module(module)
        else:
            raise Exception(f"Failed to load {cfg_file}")

        if "config" in module.__dict__:
            module.__dict__["config"](cfg)
        else:
            raise Exception(f"{cfg_file} is not a valid TBot configuration!")
