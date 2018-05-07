"""
Exports for toolchains
----------------------
"""
import tbot

EXPORT = ["Toolchain", "UnknownToolchainException"]


class UnknownToolchainException(Exception):
    """ The toolchain provided was not found in the config """
    pass


class Toolchain:
    """
    A meta object to represent a toolchain.
    Can be created with :func:`~tbot.builtin.toolchain.toolchain_get`
    """

    def __init__(self, name: str, host: str, cfg: tbot.config.Config) -> None:
        self.name = name
        self.host = host
        self.env_setup_script = cfg[f"build.{host}.toolchains.{name}.env_setup_script"]
        self.path = cfg[f"build.{host}.toolchains.{name}.path", None]
        self.prefix = cfg[f"build.{host}.toolchains.{name}.prefix", None]
