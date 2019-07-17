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
import collections
import contextlib
import copy
import re
import sys
import time
import typing
import tbot

ChanIO = typing.TypeVar("ChanIO", bound="ChannelIO")


class ChannelClosedException(Exception):
    pass


class ChannelIO(typing.ContextManager):
    __slots__ = ()

    # generic channel interface {{{
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

        :rtype: bool
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

    # }}}

    def __enter__(self: ChanIO) -> ChanIO:
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:  # type: ignore
        self.close()


def _debug_log(data: bytes, is_out: bool = False) -> bytes:
    if tbot.log.VERBOSITY >= tbot.log.Verbosity.CHANNEL:
        json_data: str
        try:
            json_data = data.decode("utf-8")
        except UnicodeDecodeError:
            json_data = data.decode("latin1")

        msg = tbot.log.c(repr(data)[1:])
        tbot.log.EventIO(
            ["__debug__"],
            (
                tbot.log.c("> ").blue.bold + msg.blue
                if is_out
                else tbot.log.c("< ").yellow.bold + msg.yellow
            ),
            verbosity=tbot.log.Verbosity.CHANNEL,
            direction="send" if is_out else "recv",
            data=json_data,
        )

    return data


class ChannelBorrowedException(Exception):
    def __str__(self) -> str:
        return "This channel is currently borrowed by another machine."


class ChannelTakenException(Exception):
    def __str__(self) -> str:
        return "Another machine has taken this channel.  It can no longer from here."


class ChannelBorrowed(ChannelIO):
    exception: typing.Type[Exception] = ChannelBorrowedException

    def write(self, buf: bytes) -> int:
        raise self.exception()

    def read(self, n: int, timeout: typing.Optional[float] = None) -> bytes:
        raise self.exception()

    def close(self) -> None:
        raise self.exception()

    def fileno(self) -> int:
        raise self.exception()

    @property
    def closed(self) -> bool:
        raise self.exception()

    def update_pty(self, columns: int, lines: int) -> None:
        raise self.exception()


class ChannelTaken(ChannelBorrowed):
    exception = ChannelTakenException

    def close(self) -> None:
        pass

    @property
    def closed(self) -> bool:
        return True


class BoundedPattern:
    __slots__ = ("pattern", "_length")

    def __init__(self, pattern: typing.Pattern[bytes]) -> None:
        self.pattern = pattern

        import sre_parse

        parsed = sre_parse.parse(
            typing.cast(str, self.pattern.pattern), flags=self.pattern.flags
        )
        width = parsed.getwidth()
        if isinstance(width, int):
            self._length = width
        elif isinstance(width, tuple):
            self._length = width[1]

        if self._length == getattr(sre_parse, "MAXREPEAT", 2 ** 32 - 1):
            raise Exception(f"Expression {self.pattern.pattern!r} is not bounded")

    def __len__(self) -> int:
        return self._length


SearchString = typing.Union[bytes, BoundedPattern]
ConvenientSearchString = typing.Union[SearchString, typing.Pattern, str]


def _convert_search_string(string: ConvenientSearchString) -> SearchString:
    if isinstance(string, str):
        return string.encode()
    elif isinstance(string, typing.Pattern):
        return BoundedPattern(string)
    else:
        return string


class DeathStringException(Exception):
    __slots__ = "string"

    def __init__(self, string: bytes):
        self.string = string

    def __repr__(self) -> str:
        return f"DeathStringException({self.string!r})"


class Channel(typing.ContextManager):
    __slots__ = ("_c", "prompt", "death_strings", "_ringbuf")

    def __init__(self, channel_io: ChannelIO) -> None:
        self._c = channel_io
        self.prompt: typing.Optional[SearchString] = None
        self.death_strings: typing.List[SearchString] = []
        self._ringbuf: typing.Deque[int] = collections.deque([], maxlen=2)

    # raw byte-level IO {{{
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
        if n < 0:
            # Block first and then read non-blocking
            buf = bytearray(self._c.read(self.READ_CHUNK_SIZE, timeout))
            self._check(buf)
            reader = self.read_iter(timeout=0.0)
        else:
            # Read n bytes non-blocking
            buf = bytearray()
            reader = self.read_iter(max=n, timeout=timeout)

        try:
            for chunk in reader:
                buf += chunk
        except TimeoutError:
            if n != -1:
                raise

        assert (n == -1) or (len(buf) == n)
        return buf

    def read_iter(
        self, max: int = sys.maxsize, timeout: typing.Optional[float] = None
    ) -> typing.Iterator[bytes]:
        start_time = time.clock()

        bytes_read = 0
        while True:
            timeout_remaining = None
            if timeout is not None:
                timeout_remaining = timeout - (time.clock() - start_time)
                if timeout <= 0:
                    raise TimeoutError()

            max_read = min(self.READ_CHUNK_SIZE, max - bytes_read)
            new = self._c.read(max_read, timeout_remaining)
            bytes_read += len(new)
            self._check(new)
            yield new

            assert bytes_read <= max, "read overflow"
            if bytes_read == max:
                break

    # }}}

    # file-like interface {{{
    def fileno(self) -> int:
        """
        Return a file descriptor which represents this channel.

        :rtype: int
        """
        return self._c.fileno()

    def close(self) -> None:
        """
        Close this channel.

        The following is always true:

            channel.close()
            assert channel.closed
        """
        self._c.close()

    @property
    def closed(self) -> bool:
        """
        Whether this channel was already closed.

        .. warning::
            A ``channel.write()`` immediately after checking ``channel.closed`` might
            still fail in the unlucky case where the remote end closed the channel just
            in between the two calls.
        """
        return self._c.closed

    # }}}

    # context manager {{{
    def __enter__(self) -> "Channel":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:  # type: ignore
        self.close()

    # }}}

    # death string handling {{{

    # Channel keeps a ringbuffer with enough space to match the longest death-string
    # and checks it for each chunk of data coming in.  If any of the strings matches,
    # the channel will throw an exception.

    @contextlib.contextmanager
    def with_death_string(
        self, string_in: ConvenientSearchString
    ) -> "typing.Iterator[Channel]":
        string = _convert_search_string(string_in)

        previous_length = typing.cast(int, self._ringbuf.maxlen)
        self.death_strings.insert(0, string)
        new_length = len(string) * 2
        if new_length > previous_length:
            self._ringbuf = collections.deque(self._ringbuf, maxlen=new_length)

        try:
            yield self
        finally:
            self.death_strings.remove(string)
            if new_length > previous_length:
                self._ringbuf = collections.deque(self._ringbuf, maxlen=previous_length)

    def _check(self, incoming: bytes) -> None:
        if self.death_strings == []:
            return

        # Chunk size is the longest death-string.
        chunk_size = typing.cast(int, self._ringbuf.maxlen) // 2

        for chunk in (
            incoming[i : i + chunk_size] for i in range(0, len(incoming), chunk_size)
        ):
            self._ringbuf.extend(chunk)
            ringbuf_bytes = bytes(self._ringbuf)

            for string in self.death_strings:
                if isinstance(string, bytes):
                    if string in ringbuf_bytes:
                        raise DeathStringException(string)
                elif isinstance(string, BoundedPattern):
                    match = string.pattern.search(ringbuf_bytes)
                    if match is not None:
                        raise DeathStringException(match[0])

    # }}}

    # pexpect-like interface {{{
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

    # prompt handling {{{
    @contextlib.contextmanager
    def with_prompt(
        self, prompt_in: ConvenientSearchString
    ) -> "typing.Iterator[Channel]":
        prompt = _convert_search_string(prompt_in)

        # If the prompt is a pattern, we need to recompile it with an additional $ in the
        # end to ensure that it only matches the end of the stream
        if isinstance(prompt, BoundedPattern):
            new_pattern = re.compile(
                prompt.pattern.pattern + b"$", prompt.pattern.flags
            )
            prompt = BoundedPattern(new_pattern)

        previous = self.prompt
        self.prompt = prompt
        try:
            yield self
        finally:
            self.prompt = previous

    def read_until_prompt(
        self,
        prompt: typing.Optional[ConvenientSearchString] = None,
        timeout: typing.Optional[float] = None,
    ) -> str:
        if prompt is not None:
            ctx = self.with_prompt(prompt)
        else:
            ctx = contextlib.nullcontext()  # type: ignore

        buf = bytearray()

        with ctx:
            for new in self.read_iter(timeout=timeout):
                buf += new

                if isinstance(self.prompt, bytes):
                    if buf.endswith(self.prompt):
                        break
                elif isinstance(self.prompt, BoundedPattern):
                    if self.prompt.pattern.search(buf) is not None:
                        break

        return buf.decode()

    # }}}

    # borrowing & taking {{{
    @contextlib.contextmanager
    def borrow(self) -> "typing.Iterator[Channel]":
        chan_io = self._c
        try:
            self._c = ChannelBorrowed()
            new = copy.deepcopy(self)
            new._c = chan_io
            yield new

            # TODO: Maybe don't allow exceptions here?
        finally:
            self._c = chan_io

    def take(self) -> "Channel":
        chan_io = self._c
        self._c = ChannelTaken()
        new = copy.deepcopy(self)
        new._c = chan_io
        return new

    # }}}
