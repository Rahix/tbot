import typing
from tbot import machine


class CommandFailedException(Exception):
    """Command that was issued did not finish successfully."""

    def __init__(
        self,
        host: machine.Machine,
        command: str,
        stdout: typing.Optional[str],
        *args: typing.Any,
    ) -> None:
        """
        Command that was issued did not finish successfully.

        :param machine.Machine host: The machine the command was issued on
        :param str command: The command that failed
        :param str stdout: Optional output of the command
        """
        super().__init__(*args)
        self.host = host
        self.command = command
        self.stdout = stdout

    def __str__(self) -> str:
        return f"[{self.command}] failed!"


class WrongHostException(Exception):
    """The host associated with an object did not match."""

    def __init__(self, host: machine.Machine, arg: typing.Any) -> None:
        """
        Create a new WrongHostException.

        :param machine.Machine host: The wrong host
        :param arg: The object that is not associated with host
        """
        super().__init__()
        self.host = host
        self.arg = arg

    def __str__(self) -> str:
        return f"{self.arg!r} is not associated with {self.host!r}"
