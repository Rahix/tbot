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
import itertools
import re
import select
import sys
import termios
import time
import tty
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


_CHANID_COLORS = ["red", "green", "yellow", "blue", "magenta", "cyan"]


def _debug_log(chan: ChannelIO, data: bytes, is_out: bool = False) -> bytes:
    if tbot.log.VERBOSITY >= tbot.log.Verbosity.CHANNEL:
        json_data = data.decode("utf-8", errors="replace")

        # Find a color for this channel to make distinguishing them easier
        chanid_color = _CHANID_COLORS[(id(chan) >> 6) % len(_CHANID_COLORS)]
        chanid = tbot.log.c(f"{id(chan) & 0xffffff:x}")
        chanid_colored = "(" + getattr(chanid, chanid_color).dark + ")"

        msg = tbot.log.c(repr(data)[1:])
        tbot.log.EventIO(
            ["__debug__"],
            (
                chanid_colored + tbot.log.c("> ").blue.bold + msg.blue
                if is_out
                else chanid_colored + tbot.log.c("< ").yellow.bold + msg.yellow
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
        return "Another machine has taken this channel.  It can no longer be accessed from here."


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
    exception: typing.Type[Exception] = ChannelTakenException

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
    __slots__ = "match"

    def __init__(self, match: typing.Union[bytes, typing.Match[bytes]] = b""):
        self.match = match

    def __repr__(self) -> str:
        return f"DeathStringException({self.match!r})"


class ExpectResult(typing.NamedTuple):
    """
    Result from a call to :py:meth:`~tbot.machine.channel.Channel.expect`.
    """

    i: int
    """
    Index into the pattern list of the matched pattern (if a list was passed to
    :py:meth:`~tbot.machine.channel.Channel.expect`).
    """

    match: typing.Union[str, typing.Match[bytes]]
    """
    Match object if the pattern was a regex-pattern or the literal if the
    pattern was a ``str`` or ``bytes``.
    """

    before: str
    """Everything from the input stream before the match, up to the matched pattern."""

    after: str
    """Any potential bytes which were read following the matched pattern."""


class Channel(typing.ContextManager):
    __slots__ = (
        "_c",
        "_log_prompt",
        "_ringbuf",
        "_stream",
        "_streambuf",
        "death_strings",
        "prompt",
    )

    def __init__(self, channel_io: ChannelIO) -> None:
        self._c = channel_io
        self.prompt: typing.Optional[SearchString] = None
        self.death_strings: typing.List[
            typing.Tuple[SearchString, typing.Type[DeathStringException]]
        ] = []
        self._ringbuf: typing.Deque[int] = collections.deque([], maxlen=2)
        self._streams: typing.List[typing.TextIO] = []
        self._streambuf = bytearray()
        self._log_prompt = True
        self._write_blacklist: typing.List[int] = []

    # raw byte-level IO {{{
    def write(self, buf: bytes, _ignore_blacklist: bool = False) -> None:
        """
        Write some bytes to this channel.

        ``write()`` ensures the whole buffer was written.  If this was not possible,
        it will throw an exception.

        :param bytes buf: Buffer with bytes to be written.
        :raises ChannelClosedException:  If the channel was closed previous to, or
            during writing.
        """
        if not _ignore_blacklist:
            for blacklisted in self._write_blacklist:
                if blacklisted in buf:
                    raise Exception(
                        f"Attempting to write a forbidden byte ({chr(blacklisted)!r})!"
                    )

        cursor = 0
        while cursor < len(buf):
            bytes_written = self._c.write(buf[cursor:])
            cursor += bytes_written

    # Size of individual read calls.
    READ_CHUNK_SIZE = 4096

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
            self._write_stream(buf)
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
        """
        Iterate over chunks of bytes read from the channel.

        ``read_iter`` reads at most ``max`` bytes from the channel before the
        iterator is exhausted.  If ``timeout`` is not ``None`` and expires
        before ``max`` bytes could be read, the next iteration attempt will
        raise an exception.

        :param int max: Maximum number of bytes to read.
        :param float timeout: Optional timeout.
        """
        start_time = time.monotonic()

        bytes_read = 0
        while True:
            timeout_remaining = None
            if timeout is not None:
                timeout_remaining = timeout - (time.monotonic() - start_time)
                if timeout_remaining <= 0:
                    raise TimeoutError()

            max_read = min(self.READ_CHUNK_SIZE, max - bytes_read)
            new = self._c.read(max_read, timeout_remaining)
            bytes_read += len(new)
            self._write_stream(new)
            self._check(new)
            yield new

            assert bytes_read <= max, "read overflow"
            if bytes_read == max:
                break

    # }}}

    # log-event streams {{{
    @contextlib.contextmanager
    def with_stream(
        self, stream: typing.TextIO, show_prompt: bool = True
    ) -> "typing.Iterator[Channel]":
        """
        Attatch a stream to this channel.

        All data read from the channel will also be sent to the stream.  This
        can be used, for example, to capture the entire boot-log of a board.
        ``with_stream`` should be used as a context-manager:

        .. code-block:: python

            import tbot

            with tbot.log.message("Output: ") as ev, chan.with_stream(ev):
                # During this context block, output is captured into `ev`
                ...

        :param io.TextIOBase stream: The stream to attach.
        :param bool show_prompt: Whether the currently configured prompt should
                                 also be sent to the stream if detected.
        """
        previous_log_prompt = self._log_prompt

        try:
            self._streams.append(stream)
            self._log_prompt = show_prompt
            yield self
        finally:
            self._streams.remove(stream)

            # If we don't want to log the prompt, advance the buffer to skip the
            # prompt string.
            if not self._log_prompt and self.prompt is not None:
                try:
                    self._streambuf = self._streambuf[len(self.prompt) :]
                except IndexError:
                    self._streambuf = bytearray()

            self._log_prompt = previous_log_prompt

    def _write_stream(self, buf: bytes) -> None:
        if self._streams != []:
            if self._log_prompt or self.prompt is None:
                for stream in self._streams:
                    stream.write(buf.decode("utf-8", errors="replace"))
            else:
                self._streambuf += buf
                if isinstance(self.prompt, bytes):
                    # Peek ahead and check whether the end of the stream matches
                    # the beginning of the prompt
                    maxlen = min(len(self.prompt), len(self._streambuf))
                    length = maxlen
                    for i in reversed(range(1, maxlen + 1)):
                        if self._streambuf[-i:] == self.prompt[:i]:
                            break
                        length = i - 1

                    if length != 0:
                        fragment = self._streambuf[:-length]
                    else:
                        fragment = self._streambuf

                    for stream in self._streams:
                        stream.write(fragment.decode("utf-8", errors="replace"))

                    if length != 0:
                        self._streambuf = self._streambuf[-length:]
                    else:
                        self._streambuf.clear()
                else:
                    # Naive approach when we can't guess whether the start of
                    # the prompt might be included in the output
                    fragment = self._streambuf[: -len(self.prompt)]
                    for stream in self._streams:
                        stream.write(fragment.decode("utf-8", errors="replace"))
                    self._streambuf = self._streambuf[-len(self.prompt) :]

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

        .. code-block:: python

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

    def add_death_string(
        self,
        string_in: ConvenientSearchString,
        exception_type: typing.Optional[typing.Type[DeathStringException]] = None,
    ) -> None:
        string = _convert_search_string(string_in)

        if exception_type is None:
            exception_type = DeathStringException

        previous_length = typing.cast(int, self._ringbuf.maxlen)
        self.death_strings.insert(0, (string, exception_type))
        new_length = len(string) * 2
        if new_length > previous_length:
            self._ringbuf = collections.deque(self._ringbuf, maxlen=new_length)

    @contextlib.contextmanager
    def with_death_string(
        self,
        string_in: ConvenientSearchString,
        exception_type: typing.Optional[typing.Type[DeathStringException]] = None,
    ) -> "typing.Iterator[Channel]":
        string = _convert_search_string(string_in)

        if exception_type is None:
            exception_type = DeathStringException

        previous_length = typing.cast(int, self._ringbuf.maxlen)
        self.death_strings.insert(0, (string, exception_type))
        new_length = len(string) * 2
        if new_length > previous_length:
            self._ringbuf = collections.deque(self._ringbuf, maxlen=new_length)

        try:
            yield self
        finally:
            self.death_strings.remove((string, exception_type))
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

            for string, exception_type in self.death_strings:
                if isinstance(string, bytes):
                    if string in ringbuf_bytes:
                        raise exception_type(string)
                elif isinstance(string, BoundedPattern):
                    match = string.pattern.search(ringbuf_bytes)
                    if match is not None:
                        raise exception_type(match[0])
                else:
                    raise AssertionError(
                        f"death string has unknown type: {string.__class__!r}"
                    )

    # }}}

    # pexpect-like interface {{{
    def send(
        self,
        s: typing.Union[str, bytes],
        read_back: bool = False,
        timeout: typing.Optional[float] = None,
        _ignore_blacklist: bool = False,
    ) -> None:
        """
        Send data to this channel.

        Send ``s`` to this channel and optionally read it back (to not clobber
        the next read).

        :param str,bytes s: Data to send.  A ``str`` will be encoded as UTF-8.
        :param bool read_back: Whether to read back the sent data.
        :param float timeout: Optional timeout for reading back data.
        """
        # Do nothing for empty strings
        if s == "" or s == b"":
            return

        s = s.encode("utf-8") if isinstance(s, str) else s
        self.write(s, _ignore_blacklist=_ignore_blacklist)

        if read_back:
            # Read back what was just sent.  Assume a well-behaved other side
            # and read two characters for every '\r' or '\n' sent.  This might
            # be flawed in some cases, though ...
            length = len(s) + s.count(b"\r") + s.count(b"\n")
            self.read(n=length, timeout=timeout)

    def sendline(
        self,
        s: typing.Union[str, bytes] = "",
        read_back: bool = False,
        timeout: typing.Optional[float] = None,
    ) -> None:
        """
        Send data to this channel and terminate with a newline.

        Send ``s`` and a newline (``\\r``) to this channel and optionally read
        it back (to not clobber the next read).

        :param str,bytes s: Data to send.  A ``str`` will be encoded as UTF-8.
        :param bool read_back: Whether to read back the sent data.
        :param float timeout: Optional timeout for reading back data.
        """
        s = s.encode("utf-8") if isinstance(s, str) else s
        # The "Enter" key sends '\r'
        self.send(s + b"\r", read_back, timeout)

    def sendcontrol(self, c: str) -> None:
        """
        Send a control-character to this terminal.

        ``c`` is the keyboard key which would need to be pressed (for example
        ``C`` for ``CTRL-C``).  See `C0 and C1 control codes`_ for more info.

        .. _C0 and C1 control codes: https://en.wikipedia.org/wiki/C0_and_C1_control_codes

        :param str c: Control character to send.
        """
        assert len(c) == 1, "Only a single character is allowed for sendcontrol()"

        num = ord(c) - 64
        assert 0 <= num <= 0x1F, f"Character {c!r} does not represent a control char!"

        self.write(bytes([num]), _ignore_blacklist=True)

    def sendeof(self) -> None:
        raise NotImplementedError()

    def sendintr(self) -> None:
        """Send ``CTRL-C`` to this channel."""
        self.sendcontrol("C")

    def readline(
        self,
        timeout: typing.Optional[float] = None,
        lineending: typing.Union[str, bytes] = "\r\n",
    ) -> str:
        """
        Read until the next line ending.

        **Example**:

        .. code-block:: python

            ch.sendline("echo Hello; echo World", read_back=True)
            assert ch.readline() == "Hello\\n"
            assert ch.readline() == "World\\n"
        """

        if isinstance(lineending, str):
            end = lineending.encode("utf-8")
        else:
            end = lineending

        # This implementation is quite naive but any
        # other way would possibly read too much :/

        start_time = time.monotonic()
        line = bytearray()

        while True:
            timeout_remaining = None
            if timeout is not None:
                timeout_remaining = timeout - (time.monotonic() - start_time)

            c = self.read(1, timeout=timeout_remaining)
            line.extend(c)

            if line.endswith(end):
                break

        return (
            line.decode("utf-8", errors="replace")
            .replace("\r\n", "\n")
            .replace("\n\r", "\n")
        )

    def expect(
        self,
        patterns: typing.Union[
            ConvenientSearchString, typing.List[ConvenientSearchString]
        ],
        timeout: typing.Optional[float] = None,
    ) -> ExpectResult:
        """
        Wait for a pattern to appear in the incoming data.

        This method is similar to `pexpect`_'s ``expect()`` although there are
        a few important differences.

        ``expect()`` will read ahead in the input stream until one of the
        patterns in ``patterns`` matches or, if not ``None``, the ``timeout``
        expires.  It might read further than the given pattern, if the input
        contains follow-up bytes in the same chunk of data.

        Different to `pexpect`_, the results are availble as an
        :ref:`channel_expect_result` (:py:class:`~tbot.machine.channel.channel.ExpectResult`)
        which is returned on match.

        :param patterns: Pattern(s) to wait for.  Can be either a single
            pattern or a list of patterns.  See :ref:`channel_search_string`
            for more info about which types can be passed as patterns.
        :param None,\\ float timeout: Optional timeout.

        .. _pexpect: https://pexpect.readthedocs.io/en/stable/overview.html
        """
        if not isinstance(patterns, list):
            pattern_list = [_convert_search_string(patterns)]
        else:
            pattern_list = [_convert_search_string(pat) for pat in patterns]

        buf = bytearray()
        for chunk in self.read_iter(timeout=timeout):
            buf.extend(chunk)

            for pattern_index, pat in enumerate(pattern_list):
                if isinstance(pat, bytes):
                    index = buf.find(pat)
                    if index != -1:
                        return ExpectResult(
                            pattern_index,
                            pat.decode("utf-8", errors="replace"),
                            buf[:index]
                            .decode("utf-8", errors="replace")
                            .replace("\r\n", "\n")
                            .replace("\n\r", "\n"),
                            buf[index + len(pat) :]
                            .decode("utf-8", errors="replace")
                            .replace("\r\n", "\n")
                            .replace("\n\r", "\n"),
                        )
                elif isinstance(pat, BoundedPattern):
                    match = pat.pattern.search(buf)
                    if match is not None:
                        return ExpectResult(
                            pattern_index,
                            match,
                            buf[: match.span(0)[0]]
                            .decode("utf-8", errors="replace")
                            .replace("\r\n", "\n")
                            .replace("\n\r", "\n"),
                            buf[match.span(0)[1] :]
                            .decode("utf-8", errors="replace")
                            .replace("\r\n", "\n")
                            .replace("\n\r", "\n"),
                        )
                else:
                    raise AssertionError(
                        f"expect pattern has unknown type: {pat.__class__!r}"
                    )

        raise Exception("reached end of stream without pattern appearing")

    # pexpect-like }}}

    # prompt handling {{{
    @contextlib.contextmanager
    def with_prompt(
        self, prompt_in: ConvenientSearchString
    ) -> "typing.Iterator[Channel]":
        """
        Set the prompt for this channel during a context.

        ``with_prompt`` is a context-manager that sets the prompt for this
        channel for the duration of a context:

        .. code-block:: python

            with chan.with_prompt("=> "):
                chan.sendline("echo Foo", read_back=True)
                # Waits for `=> `
                chan.read_until_prompt()

        :param ConvenientSearchString prompt: The new prompt pattern/string.
            See :ref:`channel_search_string` for more info.
        """
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
        """
        Read until prompt is detected.

        Read from the channel until the configured prompt string is detected.
        All data captured up until the prompt is returned, decoded as UTF-8.
        If ``prompt`` is ``None``, the prompt which was set using
        :py:meth:`tbot.machine.channel.Channel.with_prompt` is used.

        :param ConvenientSearchString prompt: The prompt to read up to.  It
            must appear as the very last readable data in the channel's data
            stream.  See :ref:`channel_search_string` for more info about which
            types can be passed for this parameter.
        :param float timeout: Optional timeout.  If ``timeout`` is set and
            expires before the prompt was detected, ``read_until_prompt``
            raises an execption.
        :rtype: str
        :returns: UTF-8 decoded string of all bytes read up to the prompt.
        """
        ctx: typing.ContextManager[typing.Any]
        if prompt is not None:
            ctx = self.with_prompt(prompt)
        else:
            # contextlib.nullcontext() would be a better fit here but sadly it
            # is only available in 3.7+
            ctx = contextlib.ExitStack()

        buf = bytearray()

        with ctx:
            for new in self.read_iter(timeout=timeout):
                buf += new

                if isinstance(self.prompt, bytes):
                    if buf.endswith(self.prompt):
                        return (
                            buf[: -len(self.prompt)]
                            .decode("utf-8", errors="replace")
                            .replace("\r\n", "\n")
                            .replace("\n\r", "\n")
                        )
                elif isinstance(self.prompt, BoundedPattern):
                    match = self.prompt.pattern.search(buf)
                    if match is not None:
                        return (
                            buf[: match.span()[0]]
                            .decode("utf-8", errors="replace")
                            .replace("\r\n", "\n")
                            .replace("\n\r", "\n")
                        )

        raise RuntimeError("unreachable")

    # }}}

    # miscellaneous {{{
    def read_until_timeout(self, timeout: typing.Optional[float]) -> str:
        """
        Read until the given timeout expires.

        This method will only return after the given timeout expires.  This can
        be useful when waiting for something to start up, but when all console
        output should still become immediately visible on stdout.

        Another use-case is waiting for a death-string to appear or a
        run-command to exit.  In those cases, pass ``None`` as timeout to make
        this method wait indefinitely.

        :param float timeout: The time to wait for, before returning.  Can be
            ``None`` to signal infinite wait time.
        :rtype: str
        :returns: All data received while waiting.
        """
        buf = bytearray()

        try:
            for new in self.read_iter(timeout=timeout):
                buf += new
        except TimeoutError:
            pass

        return (
            buf.decode("utf-8", errors="replace")
            .replace("\r\n", "\n")
            .replace("\n\r", "\n")
        )

    # }}}

    # borrowing & taking {{{
    @contextlib.contextmanager
    def borrow(self) -> "typing.Iterator[Channel]":
        """
        Temporarily borrow this channel for the duration of a context.

        **Example**:

        .. code-block:: python

            with chan.borrow() as chan2:
                # `chan` cannot be accessed inside this context
                chan2.sendline("Hello World")

            # `chan` can be accessed again here
            chan.sendintr()
        """
        chan_io = self._c
        try:
            self._c = ChannelBorrowed()
            new = copy.deepcopy(self)
            new._c = chan_io
            yield new

            # TODO: Maybe don't allow exceptions here?
        finally:
            self._c = chan_io
            # Todo mark the `new` channel as no longer accessible

    def take(self) -> "Channel":
        """
        Move ownership of this channel.

        All existing references to this channel will no longer be accessible
        after callin ``take()``.  Use this to mark transitions of a channel
        into a new (irreversible) context.  For example, when a board boots
        from U-Boot to Linux, U-Boot is no longer accessible.
        """
        chan_io = self._c
        self._c = ChannelTaken()
        new = copy.deepcopy(self)
        new._c = chan_io
        return new

    # }}}

    # interactive {{{
    def attach_interactive(
        self, end_magic: typing.Union[str, bytes, None] = None
    ) -> None:
        """
        Connect tbot's terminal to this channel.

        Allows the user to interact directly with whatever this channel is
        connected to.

        :param str, bytes end_magic: String that, when detected, should end the
            interactive session.  If no ``end_magic`` is given, pressing
            ``CTRL-D`` will terminate the session.
        """
        end_magic_bytes = (
            end_magic.encode("utf-8") if isinstance(end_magic, str) else end_magic
        )

        end_ring_buffer: typing.Deque[int] = collections.deque(
            maxlen=len(end_magic_bytes) if end_magic_bytes is not None else 1
        )

        # During an interactive session, the blacklist should not apply
        old_blacklist = self._write_blacklist
        self._write_blacklist = []

        previous: typing.Deque[int] = collections.deque(maxlen=3)

        oldtty = termios.tcgetattr(sys.stdin)
        try:
            tty.setraw(sys.stdin.fileno())
            tty.setcbreak(sys.stdin.fileno())

            mode = termios.tcgetattr(sys.stdin)
            special_chars = mode[6]
            assert isinstance(special_chars, list)
            special_chars[termios.VMIN] = b"\0"
            special_chars[termios.VTIME] = b"\0"
            termios.tcsetattr(sys.stdin, termios.TCSAFLUSH, mode)

            while True:
                r, _, _ = select.select([self, sys.stdin], [], [])

                if self in r:
                    data = self._c.read(4096)
                    if isinstance(end_magic_bytes, bytes):
                        end_ring_buffer.extend(data)
                        for a, b in itertools.zip_longest(
                            end_ring_buffer, end_magic_bytes
                        ):
                            if a != b:
                                break
                        else:
                            break
                    sys.stdout.buffer.write(data)
                    sys.stdout.buffer.flush()
                if sys.stdin in r:
                    data = sys.stdin.buffer.read(4096)
                    previous.extend(data)
                    if end_magic is None and data == b"\x04":
                        break
                    for a, b in itertools.zip_longest(previous, b"\r~."):
                        if a != b:
                            break
                    else:
                        break
                    self.send(data)

            sys.stdout.write("\r\n")
        finally:
            self._write_blacklist = old_blacklist
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, oldtty)

    # }}}
