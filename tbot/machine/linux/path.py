import os
import errno
import typing
import pathlib
from tbot.machine import linux  # noqa: F401

H = typing.TypeVar("H", bound="linux.LinuxMachine")


class Path(pathlib.PurePosixPath, typing.Generic[H]):
    __slots__ = ("_host",)

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

    def stat(self) -> os.stat_result:
        ec, stat_str = self.host.exec("stat", "-t", self)
        if ec != 0:
            raise OSError(errno.ENOENT, f"Can't stat {self}")

        stat_res = stat_str[len(self._local_str()) + 1:].split(" ")

        return os.stat_result((
            int(stat_res[2], 16),
            int(stat_res[6]),
            0,
            int(stat_res[7]),
            int(stat_res[3]),
            int(stat_res[4]),
            int(stat_res[0]),
            int(stat_res[10]),
            int(stat_res[11]),
            int(stat_res[12]),
        ))

    def exists(self) -> bool:
        return self.host.exec("test", "-e", self)[0] == 0

    def is_dir(self) -> bool:
        return self.host.exec("test", "-d", self)[0] == 0

    def is_file(self) -> bool:
        return self.host.exec("test", "-f", self)[0] == 0

    def is_symlink(self) -> bool:
        return self.host.exec("test", "-h", self)[0] == 0

    def is_block_device(self) -> bool:
        return self.host.exec("test", "-b", self)[0] == 0

    def is_char_device(self) -> bool:
        return self.host.exec("test", "-c", self)[0] == 0

    def is_fifo(self) -> bool:
        return self.host.exec("test", "-p", self)[0] == 0

    def is_socket(self) -> bool:
        return self.host.exec("test", "-S", self)[0] == 0

    def __truediv__(self, key: typing.Any) -> "Path[H]":
        return Path(self._host, super().__truediv__(key))

    def _local_str(self) -> str:
        return super().__str__()

    def __str__(self) -> str:
        return f"{self._host.name}:{super().__str__()}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._host!r}, {super().__str__()!r})"
