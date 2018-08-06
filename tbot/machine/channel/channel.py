import re
import abc
import typing
import tbot

TBOT_PROMPT = "TBOT-VEJPVC1QUk9NUFQK$ "


class ChannelClosedException(Exception):
    pass


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

    def __init__(self) -> None:
        """
        Initialize this channel so it is ready to receive commands.
        """

        # Ensure we don't make history
        self.send(
            f"""\
unset HISTFILE
PROMPT_COMMAND=''
PS1='{TBOT_PROMPT}'
"""
        )

        self.read_until_prompt(TBOT_PROMPT)

    def read_until_prompt(self, prompt: str, regex: bool = False) -> str:
        expr = f"{prompt}$" if regex else "^$"
        last_nl = 0
        buf = ""

        while True:
            buf += (
                self.recv()
                .replace("\r\n", "\n")
                .replace("\r\n", "\n")
                .replace("\r", "\n")
            )

            while "\n" in buf[last_nl:]:
                line = buf[last_nl:].split("\n")[0]
                if last_nl > 0:
                    tbot.log.message(f"   >> {line}")
                last_nl += len(line) + 1

            if (not regex and buf[-len(prompt):] == prompt) or (
                regex and re.search(expr, buf) is not None
            ):
                last_line = buf[last_nl:-len(prompt)]
                if last_line != "":
                    tbot.log.message(f"   >> {last_line}")
                break

        return buf

    def raw_command(self, command: str, *, prompt: str = TBOT_PROMPT) -> str:
        self.send(f"{command}\n")
        out = self.read_until_prompt(prompt)[
            len(command) + 1 : -len(prompt)
        ]
        return out

    def raw_command_with_retval(
        self,
        command: str,
        *,
        prompt: str = TBOT_PROMPT,
        retval_check_cmd: str = "echo $?",
    ) -> typing.Tuple[int, str]:
        out = self.raw_command(command, prompt=prompt)

        retval = int(self.raw_command(retval_check_cmd).strip())

        return retval, out
