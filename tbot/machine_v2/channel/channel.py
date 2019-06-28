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

import abc
import typing

ChanIO = typing.TypeVar("ChanIO", bound="ChannelIO")


class ChannelClosedException(Exception):
    pass


class ChannelIO(typing.ContextManager):
    __slots__ = ()

    @abc.abstractmethod
    def write(self, buf: bytes) -> None:
        """
        Write some bytes to this channel.

        ``write()`` ensures the whole buffer was written before it returns.

        :param bytes buf: Buffer with bytes to be written.
        :raises ChannelClosedException:  If the channel was closed previous to, or
            during writing.
        """
        pass

    @abc.abstractmethod
    def read(self, n: int = -1, timeout: typing.Optional[float] = None) -> bytes:
        """
        Receive somy bytes from this channel.

        If ``n`` is ``-1``, ``read()`` will wait until at least one byte is available
        and will then return all available bytes.  Otherwise it will wait until exactly
        ``n`` bytes could be read.  If timeout is not None and expires before this is
        the case, ``read()`` will raise an exception.

        .. warning::
            ``read()`` does not ensure that the returned bytes end with the end of a
            Unicode character boundary.  This means, decoding as Unicode can fail and
            code using ``read()`` should be prepared to deal with this case.

        :param int n: Number of bytes to read.  If ``n`` is not ``-1``, ``read()`` will
            return **exactly** ``n`` bytes.  If ``n`` is ``-1``, at least one byte is
            returned.
        :param float timeout:  Optional timeout.  If ``timout`` is not ``None``, ``read()``
            will return early after ``timeout`` seconds.
        :rtype: bytes
        """
        pass

    @abc.abstractmethod
    def close(self) -> None:
        """
        Close this channel.

        The following invariant **must** be upheld by an implementation:

            channel.close()
            assert channel.closed
        """
        pass

    @abc.abstractmethod
    def fileno(self) -> int:
        """
        Return a file descriptor which represents this channel.

        :rtype: int
        """
        pass

    @property
    @abc.abstractmethod
    def closed(self) -> bool:
        """
        Whether this channel was already closed.

        .. warning::
            A ``channel.write()`` immediately after checking ``channel.closed`` might
            still fail in the unlucky case where the remote end closed the channel just
            in between the two calls.
        """
        pass

    @abc.abstractmethod
    def update_pty(self, columns: int, lines: int) -> None:
        """
        Update the terminal window size of this channel.

        Channels lacking this functionality should silently ignore this call.

        :param int colums: The new width of the pty.
        :param int lines: The new height of the pty.
        """
        pass

    def __enter__(self: ChanIO) -> ChanIO:
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:  # type: ignore
        self.close()


class Channel(typing.Generic[ChanIO]):
    __slots__ = ("c",)

    def __init__(self, channel_io: ChanIO) -> None:
        self.c = channel_io

    # Standard pexpect-like interface {{{
    def send(self, s: typing.Union[str, bytes]) -> None:
        s = s.encode("utf-8") if isinstance(s, str) else s
        self.c.write(s)

    def sendline(self, s: typing.Union[str, bytes] = "") -> None:
        s = s.encode("utf-8") if isinstance(s, str) else s
        # The "Enter" key sends '\r'
        self.c.write(s + b"\r")

    def sendcontrol(self, c: str) -> None:
        assert len(c) == 1
        assert c.isalpha() or c == "@"

        self.c.write(bytes([ord(c) - 64]))

    def sendeof(self) -> None:
        raise NotImplementedError()

    def sendintr(self) -> None:
        self.sendcontrol("C")

    # TODO: Reading
    # pexpect-like }}}
