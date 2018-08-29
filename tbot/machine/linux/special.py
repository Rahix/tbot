import abc


class Special(abc.ABC):
    """Base class for special characters."""

    @abc.abstractmethod
    def resolve_string(self) -> str:
        """Return the string representation of this special character."""
        pass


class Env(Special):
    """Expand an environment variable or shell variable."""

    __slots__ = ("name",)

    def __init__(self, name: str) -> None:
        """Create a new environment variable accessor.

        :param str name: Name of the env var.
        """
        self.name = name

    def resolve_string(self) -> str:
        """Return the string representation of this special character."""
        return f"${{{self.name}}}"


class Raw(Special):
    """Raw unescaped string."""

    __slots__ = ("text",)

    def __init__(self, text: str) -> None:
        """Create a new unescaped string."""
        self.text = text

    def resolve_string(self) -> str:
        """Return the string representation of this special character."""
        return self.text


class _Static(Special):
    __slots__ = ("string",)

    def __init__(self, string: str) -> None:
        self.string = string

    def resolve_string(self) -> str:
        """Return the string representation of this special character."""
        return self.string


Pipe = _Static("|")
