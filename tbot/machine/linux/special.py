import typing
import abc
import shlex
from tbot import machine
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


class F(Special[H]):
    """Format string."""

    __slots__ = ("fmt", "args", "quote")

    def __init__(
        self,
        fmt: str,
        *args: "typing.Union[str, linux.Path[H], Special[H]]",
        quote: bool = True,
    ) -> None:
        """
        Create a format string.

        **Example**::

            m.exec0("export", linux.F("PATH={}:{}", p1, linux.Env("PATH"), quote=False))

        All normal python formatters are supported.

        :param str fmt: Format string
        :param args: Format arguments.  Can be TBot paths as well.
        :param bool quote: Whether to escape the resulting string.
        """
        self.fmt = fmt
        self.args = args
        self.quote = quote

    def resolve_string(self, host: H) -> str:
        """Return the string representation of this special character."""

        def validate(arg: typing.Union[str, linux.Path[H], Special[H]]) -> str:
            if isinstance(arg, str):
                return arg
            elif isinstance(arg, Special):
                return arg.resolve_string(host)
            elif isinstance(arg, linux.Path):
                if arg.host is not host:
                    raise machine.WrongHostException(host, arg)
                return arg._local_str()
            else:
                raise TypeError(f"{arg!r} is not a supported argument type!")

        args = list(map(validate, self.args))
        string = self.fmt.format(*args)
        if self.quote:
            return shlex.quote(string)
        else:
            return string


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
