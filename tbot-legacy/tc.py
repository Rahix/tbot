""" Dummies for pylint to shut up """
import typing
import pathlib


class GitRepository(pathlib.PurePosixPath):
    """ Dummy for pylint to shut up """
    pass


class UBootRepository(pathlib.PurePosixPath):
    """ Dummy for pylint to shut up """
    pass


class LinuxRepository(pathlib.PurePosixPath):
    """ Dummy for pylint to shut up """
    pass


class UnknownToolchainException(Exception):
    """ Dummy for pylint to shut up """
    pass


class Toolchain:
    """
    A meta object to represent a toolchain.
    Can be created with :func:`~tbot.builtin.toolchain.toolchain_get`
    """

    def __init__(self, name: str, host: str, cfg: typing.Any) -> None:
        self.name = name
        self.host = host
        self.env_setup_script = cfg[f"build.{host}.toolchains.{name}.env_setup_script"]
        self.path = cfg[f"build.{host}.toolchains.{name}.path", None]
        self.prefix = cfg[f"build.{host}.toolchains.{name}.prefix", None]


class TftpDirectory:
    """ Dummy for pylint to shut up """
    path = pathlib.PurePosixPath("/")

    def __init__(self, a: pathlib.PurePosixPath, b: pathlib.PurePosixPath) -> None:
        pass
