import abc


class Special(abc.ABC):
    @abc.abstractmethod
    def resolve_string(self) -> str:
        pass


class Env(Special):
    __slots__ = ("name",)

    def __init__(self, name: str) -> None:
        self.name = name

    def resolve_string(self) -> str:
        return f"${{{self.name}}}"


class _Pipe(Special):
    def resolve_string(self) -> str:
        return "|"


Pipe = _Pipe()
