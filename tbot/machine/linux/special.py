import typing
import abc
from tbot.machine import linux  # noqa: F401

H = typing.TypeVar("H", bound="linux.LinuxMachine")


class Special(abc.ABC, typing.Generic[H]):
    """Base class for special characters."""

    @abc.abstractmethod
    def resolve_string(self, host: H) -> str:
        """Return the string representation of this special character."""
        pass


class Raw(Special):
    """Raw unescaped string."""

    __slots__ = ("text",)

    def __init__(self, text: str) -> None:
        """
        Create a new unescaped string.

        **Example**::

            m.exec0(linux.Raw('FOOBAR="${USER}@$(hostname):${PWD}"'))

        :param str text: The raw string
        """
        self.text = text

    def resolve_string(self, _: H) -> str:
        """Return the string representation of this special character."""
        return self.text


class Env(Special):
    """Expand an environment variable or shell variable."""

    __slots__ = ("name",)

    def __init__(self, name: str) -> None:
        """
        Create a new environment variable accessor.

        **Example**::

            m.exec0(linux.Env("CC"), "-c", m.workdir / "main.c")

        :param str name: Name of the env var.
        """
        self.name = name

    def resolve_string(self, _: H) -> str:
        """Return the string representation of this special character."""
        return f"${{{self.name}}}"


class _Static(Special):
    __slots__ = ("string",)

    def __init__(self, string: str) -> None:
        self.string = string

    def resolve_string(self, _: H) -> str:
        """Return the string representation of this special character."""
        return self.string


AndThen = _Static("&&")
Background = _Static("&")
OrElse = _Static("||")
Pipe = _Static("|")
Then = _Static(";")
