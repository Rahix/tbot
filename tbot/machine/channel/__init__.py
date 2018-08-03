import abc
import typing

TBOT_PROMPT = "TBOT-VEJPVC1QUk9NUFQK$ "


class Channel(abc.ABC):
    @abc.abstractmethod
    def send(self, d: str) -> None:
        """
        Send data to the target of this channel.

        Should raise an exception if the channel is no longer available.

        :param str d: The bytes that should be sent
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
        raise NotImplementedError()

    def raw_command(self, command: str) -> str:
        raise NotImplementedError()

    def raw_command_with_retval(
        self,
        command: str,
        retval_check_cmd: str = "echo $?",
    ) -> typing.Tuple[int, str]:
        out = self.raw_command(command)

        retval = int(self.raw_command(retval_check_cmd).strip())

        return retval, out
