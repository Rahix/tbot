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
