# tbot, Embedded Automation Tool
# Copyright (C) 2018  Harald Seiler
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import errno
import typing
import pathlib
from tbot.machine import linux  # noqa: F401

H = typing.TypeVar("H", bound="linux.LinuxMachine")


class Path(pathlib.PurePosixPath, typing.Generic[H]):
    """
    A path that is associated with a tbot machine.

    A path can only be used with its associated host.  Using it with
    any other host will raise an exception and will be detected by
    a static typechecker.

    Apart from that, ``Path`` behaves like a :class:`pathlib.Path`::

        from tbot.machine import linux

        p = linux.Path(mach, "/foo/bar")
        p2 = p / "bar" / "baz"
        if not p2.exists():
            mach.exec0("mkdir", "-p", p2.parent)
            mach.exec0("touch", p2)
        elif not p2.is_file():
            raise Exception(f"{p2} must be a normal file!")
    """

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
        """
        Create a new path.

        :param linux.LinuxMachine host: Host this path should be associated with
        :param args: pathlib.PurePosixPath constructor arguments
        """
        self._host = host

    @property
    def host(self) -> H:
        """Host associated with this path."""
        return self._host

    def stat(self) -> os.stat_result:
        """
        Return the result of ``stat`` on this path.

        Tries to imitate the results of :meth:`pathlib.Path.stat`, returns a
        :class:`os.stat_result`.
        """
        ec, stat_str = self.host.exec("stat", "-t", self)
        if ec != 0:
            raise OSError(errno.ENOENT, f"Can't stat {self}")

        stat_res = stat_str[len(self._local_str()) + 1 :].split(" ")

        return os.stat_result(
            (
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
            )
        )

    def exists(self) -> bool:
        """Whether this path exists."""
        return self.host.test("test", "-e", self)

    def is_dir(self) -> bool:
        """Whether this path points to a directory."""
        return self.host.test("test", "-d", self)

    def is_file(self) -> bool:
        """Whether this path points to a normal file."""
        return self.host.test("test", "-f", self)

    def is_symlink(self) -> bool:
        """Whether this path points to a symlink."""
        return self.host.test("test", "-h", self)

    def is_block_device(self) -> bool:
        """Whether this path points to a block device."""
        return self.host.test("test", "-b", self)

    def is_char_device(self) -> bool:
        """Whether this path points to a character device."""
        return self.host.test("test", "-c", self)

    def is_fifo(self) -> bool:
        """Whether this path points to a pipe(fifo)."""
        return self.host.test("test", "-p", self)

    def is_socket(self) -> bool:
        """Whether this path points to a unix domain-socket."""
        return self.host.test("test", "-S", self)

    @property
    def parent(self) -> "Path[H]":
        """Parent of this path."""
        return Path(self._host, super().parent)

    def __truediv__(self, key: typing.Any) -> "Path[H]":
        return Path(self._host, super().__truediv__(key))

    def _local_str(self) -> str:
        return super().__str__()

    def __str__(self) -> str:
        return f"{self._host.name}:{super().__str__()}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._host!r}, {super().__str__()!r})"

    def __fspath__(self) -> str:
        raise NotImplementedError("__fspath__ does not exist for tbot paths!")
