import abc
import io
import re
import select
import sys
import termios
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
    def send(self, data: str) -> None:
        """
        Send data to the target of this channel.

        Should raise an exception if the channel is no longer available.

        :param str data: The string that should be sent
        """
        pass

    @abc.abstractmethod
    def recv(self) -> str:
        """
        Receive data from this channel.

        Should raise an exception if the channel is no longer available.

        :rtype: str
        :returns: String that have been read from this channel. Must block until
                  at least one byte is available.
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
        pass

    def _interactive_setup(self) -> None:
        pass

    def _interactive_teardown(self) -> None:
        pass

    def attach_interactive(self, end_magic: typing.Optional[str] = None) -> None:
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
                    data_string = self.recv()
                    if data_string == end_magic:
                        break
                    sys.stdout.write(data_string)
                    sys.stdout.flush()
                if sys.stdin in r:
                    data_string = sys.stdin.read(4096)
                    if end_magic is None and data_string == "\x04":
                        break
                    self.send(data_string)
            sys.stdout.write("\r\n")
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, oldtty)
            self._interactive_teardown()

    def initialize(self) -> None:
        """
        Initialize this channel so it is ready to receive commands.
        """

        # Set proper prompt
        self.raw_command(f"PROMPT_COMMAND=''; PS1='{TBOT_PROMPT}'")
        # Ensure we don't make history
        self.raw_command("unset HISTFILE")
        # Disable line editing
        self.raw_command("set +o vi")
        self.raw_command("set +o emacs")
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
    ) -> str:
        expr = f"{prompt}$" if regex else "^$"
        buf = ""

        while True:
            new = (
                self.recv()
                .replace("\r\n", "\n")
                .replace("\r\n", "\n")
                .replace("\r", "\n")
            )

            buf += new

            if (not regex and buf[-len(prompt) :] == prompt) or (
                regex and re.search(expr, buf) is not None
            ):
                if stream:
                    stream.write(new[: -len(prompt)])
                break
            elif stream:
                stream.write(new)

        return buf

    def raw_command(
        self,
        command: str,
        *,
        prompt: str = TBOT_PROMPT,
        stream: typing.Optional[typing.TextIO] = None,
    ) -> str:
        self.send(f"{command}\n")
        if stream:
            stream = SkipStream(stream, len(command) + 1)
        out = self.read_until_prompt(prompt, stream=stream)[
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
