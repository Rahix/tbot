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

TBOT_PROMPT = "TBOT-VEJPVC1QUk9NUFQK$ "


class ChannelClosedException(Exception):
    pass


class SkipStream(io.StringIO):

    def __init__(self, stream: typing.TextIO, n: int) -> None:
        self.stream = stream
        self.n = n

    def write(self, s: str) -> int:
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

    @abc.abstractmethod
    def send(self, data: typing.Union[bytes, str]) -> None:
        pass

    @abc.abstractmethod
    def recv(self, timeout: typing.Optional[float] = None) -> bytes:
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
        pass

    def _interactive_setup(self) -> None:
        pass

    def _interactive_teardown(self) -> None:
        pass

    def attach_interactive(
        self, end_magic: typing.Union[str, bytes, None] = None
    ) -> None:
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

    def initialize(self, *, shell: str = "bash") -> None:
        """
        Initialize this channel so it is ready to receive commands.
        """

        # Set proper prompt
        self.send("PROMPT_COMMAND=''\n")
        self.raw_command(f"PS1='{TBOT_PROMPT}'")
        # Ensure we don't make history
        self.raw_command("unset HISTFILE")
        # Disable line editing
        if shell == "bash":
            self.raw_command("set +o vi")
            self.raw_command("set +o emacs")
        # elif shell == "ash" or shell == "dash":
        #     self.raw_command("set +o interactive")
        else:
            # No shell specific behaviour known, try
            # making the terminal really wide
            self.raw_command("stty cols 1024")
        # Ensure multiline commands work
        self.raw_command("PS2=''")

    def __init__(self) -> None:
        self.initialize()

    def read_until_prompt(
        self,
        prompt: str,
        *,
        regex: bool = False,
        stream: typing.Optional[typing.TextIO] = None,
        timeout: typing.Optional[float] = None,
    ) -> str:
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
    ) -> typing.Tuple[int, str]:
        out = self.raw_command(command, prompt=prompt, stream=stream)

        retval = int(self.raw_command(retval_check_cmd, prompt=prompt).strip())

        return retval, out
