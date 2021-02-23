# tbot, Embedded Automation Tool
# Copyright (C) 2019  Harald Seiler
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

import base64
import os
import errno
import typing
import pathlib
import itertools
from .. import linux  # noqa: F401
from .. import channel  # noqa: F401

H = typing.TypeVar("H", bound="linux.LinuxShell")


class PathWriteDeathStringException(channel.DeathStringException):
    pass


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

        :param linux.LinuxShell host: Host this path should be associated with
        :param args: :py:class:`pathlib.PurePosixPath` constructor arguments
        :rtype: Path
        :returns: A path associated with host
        """
        return super().__new__(cls, *args)

    def __init__(self, host: H, *args: typing.Any) -> None:
        """
        Create a new path.

        :param linux.LinuxShell host: Host this path should be associated with
        :param args: :py:class:`pathlib.PurePosixPath` constructor arguments
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

    def glob(self, pattern: str) -> "typing.Iterator[Path[H]]":
        """
        Iterate over this subtree and yield all existing files (of any
        kind, including directories) matching the given relative pattern.

        **Example**:

        .. code-block:: python

            ubootdir = lh.workdir / "u-boot"

            # .glob() returns a list which can be iterated.
            for f in ubootdir.glob("common/*.c"):
                tbot.log.message(f"Found {f}.")

            # To use the globs in another commandline (note the `*`!):
            lh.exec0("ls", "-l", *ubootdir.glob("common/*.c"))

        .. warning::

            The glob pattern **must not contain spaces or other special characters**!
        """
        fullpath = self.host.escape(self._local_str()) + "/" + pattern

        output = self.host.exec0("printf", "%s\\n", linux.Raw(fullpath))

        for line in output[:-1].split("\n"):
            yield Path(self._host, line)

    def write_text(
        self,
        data: str,
        encoding: typing.Optional[str] = None,
        errors: typing.Optional[str] = None,
    ) -> int:
        """
        Write ``data`` into the file this path points to.

        **Example**:

        .. code-block:: python

            f = lnx.workdir / "foo.sh"

            f.write_text('''\\
            #!/bin/sh
            set -e

            echo "Hello tbot!"
            ps ax
            ''')

            f.exec0("chmod", "+x", f)

        .. warning::

            This string must contain 'text' in the sense that some control
            characters are not allowed.  Consult the documentation of
            :py:meth:`LinuxShell.run() <tbot.machine.linux.LinuxShell.run>` for
            details.

            Additionally, line-endings might be transformed according to the
            tty's settings.  This function is not meant for byte-by-byte
            transfers, but for configuration files or small scripts.  If you
            want to transfer a blob or a larger file, consider using
            :py:func:`tbot.tc.shell.copy` or (for small files)
            :py:meth:`Path.write_bytes() <tbot.machine.linux.Path.write_bytes>`.
        """
        if not isinstance(data, str):
            raise TypeError(f"data must be str, not {data.__class__.__name__}")
        byte_data = data.encode(encoding or "utf-8", errors or "strict")

        with self.host.run(
            "tee", self, linux.RedirStdout(self.host.fsroot / "/dev/null")
        ) as ch:
            with ch.with_death_string("tee: ", PathWriteDeathStringException):
                try:
                    ch.send(byte_data, read_back=True)

                    # Send ^D twice if the file does not end with a line ending.  This
                    # is necessary to make `tee` notice the EOF correctly.
                    if not (byte_data == b"" or byte_data[-1:] in [b"\n", b"\r"]):
                        ch.sendcontrol("D")
                except PathWriteDeathStringException:
                    pass

                ch.sendcontrol("D")
                ch.terminate0()

        return len(byte_data)

    def read_text(
        self, encoding: typing.Optional[str] = None, errors: typing.Optional[str] = None
    ) -> str:
        """
        Read the contents of a *text* file, pointed to by this path.

        .. warning::

            This method is for 'text' content only as line-endings might not be
            transferred as contained in the file (Will always use a single
            ``\\n``).  If you want to transfer a file byte-by-byte, consider
            using :py:func:`tbot.tc.shell.copy` instead.  For small files,
            :py:meth:`Path.write_bytes() <tbot.machine.linux.Path.read_bytes>`
            might also be an option.
        """
        if encoding is not None or errors is not None:
            raise NotImplementedError("Encoding is not implemented for `read_text`")

        return self.host.exec0("cat", self)

    def write_bytes(self, data: bytes) -> int:
        """
        Write binary ``data`` into the file this path points to.

        .. note::

            This method ensures exact byte-by-byte transfer.  To do so, it
            encodes the data using base64 which makes console output less
            readable.  If you intend to transfer text data, please use
            :py:meth:`Path.write_text() <tbot.machine.linux.Path.write_text>`.
        """
        if not isinstance(data, bytes):
            raise TypeError(f"data must be bytes, not {data.__class__.__name__}")

        with self.host.run(
            *["base64", "-d", "-"],
            linux.Pipe,
            "tee",
            self,
            linux.RedirStdout(self.host.fsroot / "/dev/null"),
        ) as ch:
            with ch.with_death_string("tee: ", PathWriteDeathStringException):
                try:
                    # Encode as base64 and split into 76 character lines.  This makes
                    # output more readable and does not affect parsing on the remote
                    # end.
                    encoded = iter(base64.b64encode(data))
                    while True:
                        chunk = bytes(itertools.islice(encoded, 76))

                        if chunk == b"":
                            break

                        ch.sendline(chunk, read_back=True)
                except PathWriteDeathStringException:
                    pass

                ch.sendcontrol("D")
                ch.terminate0()

        return len(data)

    def read_bytes(self) -> bytes:
        """
        Read the contents of a file, pointed to by this path.

        .. note::

            This method ensures exact byte-by-byte transfer.  To do so, it
            encodes the data using base64 which makes console output less
            readable.  If you intend to transfer text data, please use
            :py:meth:`Path.read_text() <tbot.machine.linux.Path.read_text>`.
        """
        encoded = self.host.exec0("base64", self)

        return base64.b64decode(encoded)

    def __truediv__(self, key: typing.Any) -> "Path[H]":
        return Path(self._host, super().__truediv__(key))

    def _local_str(self) -> str:
        return super().__str__()

    def __str__(self) -> str:
        return f"{self._host.name}:{super().__str__()}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._host!r}, {super().__str__()!r})"

    # __fspath__ does not make sense for tbot paths as they don't represent
    # a path on the local filesystem.
    __fspath__ = None  # type: ignore
