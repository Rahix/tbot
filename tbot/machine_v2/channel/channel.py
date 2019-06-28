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
import time
import typing

ChanIO = typing.TypeVar("ChanIO", bound="ChannelIO")


class ChannelClosedException(Exception):
    pass


class ChannelIO(typing.ContextManager):
    __slots__ = ()

    @abc.abstractmethod
    def write(self, buf: bytes) -> int:
        """
        Write some bytes to this channel.

        ``write()`` returns the number of bytes written.  This number might be lower
        than ``len(buf)``.

        :param bytes buf: Buffer with bytes to be written.
        :raises ChannelClosedException:  If the channel was closed previous to, or
            during writing.
        """
        pass

    @abc.abstractmethod
    def read(self, n: int, timeout: typing.Optional[float] = None) -> bytes:
        """
        Receive somy bytes from this channel.

        Return at most ``n`` bytes, but at least 1 (if ``n`` is not ``0``).  Raise an
        exception if ``timeout`` is not ``None`` and expires before data was received.

        :param int n: Maximum number of bytes to read.
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
    __slots__ = ("_c",)

    def __init__(self, channel_io: ChanIO) -> None:
        self._c = channel_io

    # Raw byte-level IO {{{
    def write(self, buf: bytes) -> None:
        """
        Write some bytes to this channel.

        ``write()`` ensures the whole buffer was written.  If this was not possible,
        it will throw an exception.

        :param bytes buf: Buffer with bytes to be written.
        :raises ChannelClosedException:  If the channel was closed previous to, or
            during writing.
        """
        cursor = 0
        while cursor < len(buf):
            bytes_written = self._c.write(buf[cursor:])
            cursor += bytes_written

    READ_CHUNK_SIZE = 4096
    """Size of individual read calls."""

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
        start_time = time.clock()

        max_read = min(self.READ_CHUNK_SIZE, n) if n > 0 else self.READ_CHUNK_SIZE
        buf = self._c.read(max_read, timeout)

        while True:
            max_read = (
                min(self.READ_CHUNK_SIZE, n - len(buf))
                if n > 0
                else self.READ_CHUNK_SIZE
            )
            if max_read == 0:
                # The end of an exact read.
                break

            if timeout is not None:
                timeout_remaining = timeout - (time.clock() - start_time)
                if timeout_remaining <= 0:
                    raise TimeoutError()
                new = self._c.read(max_read, timeout_remaining)
            else:
                try:
                    new = self._c.read(max_read, None if n > 0 else 0.0)
                except TimeoutError:
                    # When the user did not set a timeout, this means we have reached
                    # the end of readable data.  Return now.
                    break

            buf += new

        assert (n == -1) or (len(buf) == n)
        return buf

    # }}}

    # file-like interface {{{
    @property
    def closed(self) -> bool:
        return self._c.closed

    # }}}

    # Standard pexpect-like interface {{{
    def send(self, s: typing.Union[str, bytes]) -> None:
        s = s.encode("utf-8") if isinstance(s, str) else s
        self.write(s)

    def sendline(self, s: typing.Union[str, bytes] = "") -> None:
        s = s.encode("utf-8") if isinstance(s, str) else s
        # The "Enter" key sends '\r'
        self.write(s + b"\r")

    def sendcontrol(self, c: str) -> None:
        assert len(c) == 1
        assert c.isalpha() or c == "@"

        self.write(bytes([ord(c) - 64]))

    def sendeof(self) -> None:
        raise NotImplementedError()

    def sendintr(self) -> None:
        self.sendcontrol("C")

    # TODO: Reading
    # pexpect-like }}}
