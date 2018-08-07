import typing
import pathlib
from tbot.machine import linux  # noqa: F401

H = typing.TypeVar("H", bound="linux.LinuxMachine")


class Path(pathlib.PurePosixPath, typing.Generic[H]):
    def __new__(cls, host: H, *args: typing.Any) -> "Path":
        """
        Create a new path instance.

        :param linux.LinuxMachine host: Host this path should be associated with
        :param args: pathlib.PurePosixPath constructor arguments
        :rtype: Path
        :returns: A path associated with host
        """
        return super().__new__(cls, *args)

    def __init__(self, host: H, *args: typing.Any) -> None:
        """Initialize a path."""
        self._host = host

    @property
    def host(self) -> H:
        """Return the host associated with this path."""
        return self._host

    def __truediv__(self, key: typing.Any) -> "Path[H]":
        return Path(self._host, super().__truediv__(key))

    def _local_str(self) -> str:
        return super().__str__()

    def __str__(self) -> str:
        return f"{self._host.name}:{super().__str__()}"

    def __repr__(self) -> str:
        return f"Path({self._host!r}, {super().__str__()!r})"
