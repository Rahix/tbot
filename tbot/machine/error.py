import typing
from tbot import machine


class CommandFailedException(Exception):

    def __init__(
        self,
        host: machine.Machine,
        command: str,
        stdout: typing.Optional[str],
        *args: typing.Any,
    ) -> None:
        super().__init__(*args)
        self.host = host
        self.command = command
        self.stdout = stdout

    def __str__(self) -> str:
        return f"[{self.command}] failed!"


class WrongHostException(Exception):

    def __init__(self, host: machine.Machine, arg: typing.Any) -> None:
        super().__init__()
        self.host = host
        self.arg = arg

    def __str__(self) -> str:
        return f"{self.arg!r} is not associated with {self.host!r}"
