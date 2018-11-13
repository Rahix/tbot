import typing

class SSHConfig:
    def parse(self, f: typing.TextIO) -> None: ...
    def lookup(
        self, host: str
    ) -> typing.Dict[str, typing.Union[str, typing.List[str]]]: ...
