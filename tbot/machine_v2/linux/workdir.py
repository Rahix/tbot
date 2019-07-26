import typing

from . import path, linux_shell
from .path import H


class Workdir(path.Path[H]):
    _workdirs: "typing.Dict[typing.Tuple[linux_shell.LinuxShell, str], Workdir]" = {}

    def __init__(self) -> None:  # noqa: D107
        raise NotImplementedError(
            "You are probably using this wrong, please refer to the documentation."
        )

    @classmethod
    def static(cls, host: H, pathstr: str) -> "Workdir[H]":
        key = (host, pathstr)
        try:
            return Workdir._workdirs[key]
        except KeyError:
            p = typing.cast(Workdir, path.Path(host, pathstr))
            host.exec0("mkdir", "-p", p)
            Workdir._workdirs[key] = p
            return p

    @classmethod
    def athome(cls, host: H, subdir: str) -> "Workdir[H]":
        key = (host, subdir)
        try:
            return Workdir._workdirs[key]
        except KeyError:
            home = host.env("HOME")
            p = typing.cast(Workdir, path.Path(host, home) / subdir)
            host.exec0("mkdir", "-p", p)
            Workdir._workdirs[key] = p
            return p
