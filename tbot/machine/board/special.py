import shlex
import typing
import abc


class Special(abc.ABC):
    """Abstract base for special U-Boot characters."""

    @abc.abstractmethod
    def resolve_string(self) -> str:
        """Return the string representation of this special char."""
        pass


class Env(Special):
    """U-Boot environment variable."""

    __slots__ = ("name",)

    def __init__(self, name: str) -> None:
        """Expand the ``name`` env variable."""
        self.name = name

    def resolve_string(self) -> str:  # noqa: D102
        return f"${{{self.name}}}"


class F(Special):
    """Format string."""

    __slots__ = ("fmt", "args", "quote")

    def __init__(
        self, fmt: str, *args: typing.Union[str, Special], quote: bool = True
    ) -> None:
        """
        Create a format string.

        **Example**::

            m.exec0("setenv", "foo", board.F("0x{}", board.Env("loadaddr"), quote=False))

        All normal python formatters are supported.

        :param str fmt: Format string
        :param args: Format arguments.
        :param bool quote: Whether to escape the resulting string.
        """
        self.fmt = fmt
        self.args = args
        self.quote = quote

    def resolve_string(self) -> str:
        """Return the string representation of this special character."""

        def validate(arg: typing.Union[str, Special]) -> str:
            if isinstance(arg, str):
                return arg
            elif isinstance(arg, Special):
                return arg.resolve_string()
            else:
                raise TypeError(f"{arg!r} is not a supported argument type!")

        args = list(map(validate, self.args))
        string = self.fmt.format(*args)
        if self.quote:
            return shlex.quote(string)
        else:
            return string


class Raw(Special):
    """Raw string."""

    __slots__ = ("text",)

    def __init__(self, text: str) -> None:
        """Create a new raw unescaped string ``text``."""
        self.text = text

    def resolve_string(self) -> str:  # noqa: D102
        return self.text


class _Static(Special):
    __slots__ = ("string",)

    def __init__(self, string: str) -> None:
        self.string = string

    def resolve_string(self) -> str:
        return self.string


Then = _Static(";")
