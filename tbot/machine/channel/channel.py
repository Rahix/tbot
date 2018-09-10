import abc
import collections
import io
import itertools
import re
import select
import sys
import termios
import time
import tty
import typing

import tbot
from tbot.machine.linux import shell

TBOT_PROMPT = "TBOT-VEJPVC1QUk9NUFQK$ "


class ChannelClosedException(Exception):
    """Exception when attempting to interact with a closed channel."""

    pass


class SkipStream(io.StringIO):
    """Stream wrapper that skips a few character at the start."""

    def __init__(self, stream: typing.TextIO, n: int) -> None:
        """
        Create a new SkipStream that skips ``n`` chars.

        :param io.TextIOBase stream: The underlying stream. The first ``n`` chars
            written to this SkipStream will not be written to ``stream``.
        :param int n: Number of characters to skip.
        """
        self.stream = stream
        self.n = n

    def write(self, s: str) -> int:
        """Write some string to this stream."""
        if self.n > 0:
            if self.n > len(s):
                self.n -= len(s)
                return len(s)
            else:
                s = s[self.n :]
                n = self.n
                self.n = 0
                return self.stream.write(s) + n
        else:
            return self.stream.write(s)


class Channel(abc.ABC):
    """Generic channel."""

    @abc.abstractmethod
    def send(self, data: typing.Union[bytes, str]) -> None:
        """
        Send some data to this channel.

        :param bytes, str data: Data to be sent. It data is a :class:`str` it will
            be encoded using ``utf-8``.
        :raises ChannelClosedException: If the cannel is no longer open.
        """
        pass

    @abc.abstractmethod
    def recv(self, timeout: typing.Optional[float] = None) -> bytes:
        """
        Receive some data from this channel.

        ``recv`` will block until at least
        one byte is available or the timeout is reached.

        .. warning::
            ``recv`` does in no way attempt to ensure that bytes can be decoded
            as unicode. It is very well possible that recv returns after half a unicode
            sequence. Code using ``recv`` needs to be robust in regards to this.

            Because of this, ``recv`` should only be used if no other method of
            :class:`~tbot.machine.channel.Channel` suits your needs.

        :param float timeout: Optional timeout after which ``recv`` should return
            if no data is avalable.
        :raises ChannelClosedException: If the channel is no longer open.
        :raises TimeoutError: If the timeout was reached before data got available.
        """
        pass

    @abc.abstractmethod
    def close(self) -> None:
        """
        Close this channel.

        Calls to ``send``/``recv`` must fail after calling ``close``.
        """
        pass

    @abc.abstractmethod
    def fileno(self) -> int:
        """
        Return the filedescriptor of this channel.

        :rtype: int
        """
        pass

    @abc.abstractmethod
    def isopen(self) -> bool:
        """
        Return whether this channel is still open.

        .. warning::
            The result of this call should only be taken as a hint, as the remote
            end might unexpectedly close the channel shortly after the call.

        :rtype: bool
        """
        pass

    def _interactive_setup(self) -> None:
        """Do some setup before making a channel interactive."""
        pass

    def _interactive_teardown(self) -> None:
        """Teardown after returning from an interactive session."""
        pass

    def attach_interactive(
        self, end_magic: typing.Union[str, bytes, None] = None
    ) -> None:
        """
        Connect TBot's terminal to this channel.

        Allows the user to interact directly with whatever this channel is
        connected to.

        :param str, bytes end_magic: String that when read should end the
            interactive session.
        """
        end_magic_bytes = (
            end_magic.encode("utf-8") if isinstance(end_magic, str) else end_magic
        )

        end_ring_buffer: typing.Deque[int] = collections.deque(
            maxlen=len(end_magic_bytes) if end_magic_bytes is not None else 1
        )

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

            self._interactive_setup()

            while True:
                r, _, _ = select.select([self, sys.stdin], [], [])

                if self in r:
                    data = self.recv()
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
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, oldtty)
            self._interactive_teardown()

    def initialize(self, *, sh: typing.Type[shell.Shell] = shell.Bash) -> None:
        """
        Initialize this channel so it is ready to receive commands.

        Internally runs commands to set the prompt to a known value and disable
        history + line-editing.

        :param tbot.machine.linux.shell.Shell sh: Type of the Shell this channel
            is connected to.
        """
        # Set proper prompt
        self.raw_command(sh.set_prompt(TBOT_PROMPT))

        # Ensure we don't make history
        cmd = sh.disable_history()
        if cmd is not None:
            self.raw_command(cmd)

        # Disable line editing
        cmd = sh.disable_editing()
        if cmd is not None:
            self.raw_command(cmd)

        # Ensure multiline commands work
        cmd = sh.set_prompt2("")
        if cmd is not None:
            self.raw_command(cmd)

    def __init__(self) -> None:
        """Create a new channel."""
        self.initialize()

    def read_until_prompt(
        self,
        prompt: str,
        *,
        regex: bool = False,
        stream: typing.Optional[typing.TextIO] = None,
        timeout: typing.Optional[float] = None,
    ) -> str:
        """
        Read until receiving ``prompt``.

        :param str prompt: The prompt to wait for. If ``regex`` is ``True``, this
            will be interpreted as a regular expression.
        :param bool regex: Whether the prompt should be interpreted as is or as a
            regular expression. In the latter case, a ``'$'`` will be added to the
            end of the expression.
        :param io.TextIOBase stream: Optional stream where ``read_until_prompt``
            should write everything received up until the prompt is detected.
        :param float timeout: Optional timeout.
        :raises TimeoutError: If a timeout is set and this timeout is reached before
            the prompt is detected.
        :rtype: str
        :returns: Everything read up until the prompt.
        """
        start_time = time.monotonic()
        expr = f"{prompt}$" if regex else "^$"
        buf = ""

        timeout_remaining = timeout
        while True:
            new = (
                self.recv(timeout=timeout_remaining)
                .replace(b"\r\n", b"\n")
                .replace(b"\r\n", b"\n")
                .replace(b"\r", b"\n")
            )

            decoded = ""
            for _ in range(10):
                try:
                    decoded += new.decode("utf-8")
                    break
                except UnicodeDecodeError:
                    try:
                        new += self.recv(timeout=0.1)
                    except TimeoutError:
                        pass
            else:
                decoded += new.decode("latin_1")

            if tbot.log.VERBOSITY >= tbot.log.Verbosity.CHANNEL:
                tbot.log.EventIO(
                    tbot.log.c(repr(decoded)).yellow,
                    verbosity=tbot.log.Verbosity.CHANNEL,
                )

            buf += decoded

            if (not regex and buf[-len(prompt) :] == prompt) or (
                regex and re.search(expr, buf) is not None
            ):
                if stream:
                    stream.write(decoded[: -len(prompt)])
                break
            elif stream:
                stream.write(decoded)

            if timeout is not None:
                current_time = time.monotonic()
                timeout_remaining = timeout - (current_time - start_time)

        return buf

    def raw_command(
        self,
        command: str,
        *,
        prompt: str = TBOT_PROMPT,
        stream: typing.Optional[typing.TextIO] = None,
        timeout: typing.Optional[float] = None,
    ) -> str:
        """
        Send a command to this channel and wait until it finishes.

        :param str command: The command without a trailing newline
        :param str prompt: The prompt of the shell on this channel. This is needed
            to detect when the command is done.
        :param io.TextIOBase stream: Optional stream where the commands output
            should be written.
        :param float timeout: Optional timeout.
        :raises TimeoutError: If the timeout was reached before the command finished.
        :rtype: str
        :returns: The ouput of the command. Will contain a trailing newline unless the
            command did not send one (eg. ``printf``)
        """
        self.send(f"{command}\n".encode("utf-8"))
        if stream:
            stream = SkipStream(stream, len(command) + 1)
        out = self.read_until_prompt(prompt, stream=stream, timeout=timeout)[
            len(command) + 1 : -len(prompt)
        ]
        return out

    def raw_command_with_retval(
        self,
        command: str,
        *,
        prompt: str = TBOT_PROMPT,
        retval_check_cmd: str = "echo $?",
        stream: typing.Optional[typing.TextIO] = None,
        timeout: typing.Optional[float] = None,
    ) -> typing.Tuple[int, str]:
        """
        Send a command to this channel, wait until it finishes, and check its retcode.

        :param str command: The command without a trailing newline
        :param str prompt: The prompt of the shell on this channel. This is needed
            to detect when the command is done.
        :param str retval_check_cmd: Command used to check the exit code.
        :param io.TextIOBase stream: Optional stream where the commands output
            should be written.
        :param float timeout: Optional timeout.
        :raises TimeoutError: If the timeout was reached before the command finished.
        :rtype: tuple[int, str]
        :returns: The retcode and ouput of the command. Will contain a trailing newline
            unless the command did not send one (eg. ``printf``)
        """
        out = self.raw_command(command, prompt=prompt, stream=stream, timeout=timeout)

        retval = int(
            self.raw_command(retval_check_cmd, prompt=prompt, timeout=timeout).strip()
        )

        return retval, out
