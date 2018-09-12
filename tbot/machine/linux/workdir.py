import typing
from tbot.machine import linux

H = typing.TypeVar("H", bound=linux.LinuxMachine)


class Workdir:
    @classmethod
    def static(cls, host: H, path: str) -> linux.Path[H]:
        p = linux.Path(host, path)

        if not hasattr(host, "_wd_path"):
            if not p.is_dir():
                host.exec0("mkdir", "-p", p)

            setattr(host, "_wd_path", p)

        return typing.cast(linux.Path[H], getattr(host, "_wd_path"))

    @classmethod
    def athome(cls, host: H, subdir: str) -> linux.Path[H]:
        home = host.exec0("echo", linux.Env("HOME")).strip("\n")
        p = linux.Path(host, home) / subdir

        if not hasattr(host, "_wd_path"):
            if not p.is_dir():
                host.exec0("mkdir", "-p", p)

            setattr(host, "_wd_path", p)

        return typing.cast(linux.Path[H], getattr(host, "_wd_path"))
