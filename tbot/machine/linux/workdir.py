import typing
from tbot.machine import linux

H = typing.TypeVar("H", bound=linux.LinuxMachine)


class Workdir:
    """Helper for defining a machines workdir."""

    def __init__(self) -> None:  # noqa: D107
        raise NotImplementedError(
            "You are probably using this wrong, please refer to the documentation."
        )

    @classmethod
    def static(cls, host: H, path: str) -> linux.Path[H]:
        """
        Create a new static workdir.

        Should be used inside the :meth:`~tbot.machine.linux.LinuxMachine.workdir`
        method, like this::

            class MyMachine(...):
                ...

                @property
                def workdir(self) -> "linux.Path[MyMachine]":
                    return linux.Workdir.static(self, "/tmp/tbot-workdir")

        :param linux.LinuxMachine host: Host for which this workdir should be
            defined.
        :param str path: Fixed workdir path
        :rtype: linux.Path
        :returns: A TBot-path to the workdir
        """
        p = linux.Path(host, path)

        if not hasattr(host, "_wd_path"):
            if not p.is_dir():
                host.exec0("mkdir", "-p", p)

            setattr(host, "_wd_path", p)

        return typing.cast(linux.Path[H], getattr(host, "_wd_path"))

    @classmethod
    def athome(cls, host: H, subdir: str) -> linux.Path[H]:
        """
        Create a new workdir below the users home.

        Should be used inside the :meth:`~tbot.machine.linux.LinuxMachine.workdir`
        method, like this::

            class MyMachine(...):
                ...

                @property
                def workdir(self) -> "linux.Path[MyMachine]":
                    return linux.Workdir.athome(self, "tbot-work")

        :param linux.LinuxMachine host: Host for which this workdir should be
            defined.
        :param str subdir: Name of the subdirectory in $HOME which should be
            used as a workdir.
        :rtype: linux.Path
        :returns: A TBot-path to the workdir
        """
        home = host.exec0("echo", linux.Env("HOME")).strip("\n")
        p = linux.Path(host, home) / subdir

        if not hasattr(host, "_wd_path"):
            if not p.is_dir():
                host.exec0("mkdir", "-p", p)

            setattr(host, "_wd_path", p)

        return typing.cast(linux.Path[H], getattr(host, "_wd_path"))
