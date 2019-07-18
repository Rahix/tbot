import abc
import contextlib
import typing
from . import channel

Self = typing.TypeVar("Self", bound="Machine")


class Machine(abc.ABC):
    __slots__ = ("_cx", "ch")

    ch: channel.Channel

    @property
    @abc.abstractmethod
    def name(self) -> str:
        raise NotImplementedError("abstract method")

    # Abstract methods that will be implemented by connector and shell
    @abc.abstractmethod
    def _connect(self) -> typing.ContextManager[channel.Channel]:
        raise NotImplementedError("abstract method")

    @abc.abstractmethod
    def clone(self: Self) -> Self:
        raise NotImplementedError("abstract method")

    @abc.abstractmethod
    def _init_shell(self) -> typing.ContextManager:
        raise NotImplementedError("abstract method")

    def __enter__(self: Self) -> Self:
        self._cx = contextlib.ExitStack().__enter__()

        # This inner stack is meant to protect the __enter__() implementations
        with contextlib.ExitStack() as cx:
            # If anything goes wrong, execute this machine's __exit__()
            cx.push(self)

            # Run the connector
            self.ch = self._cx.enter_context(self._connect())

            # Run all initializers according to the MRO
            for cls in type(self).mro():
                if Initializer in cls.__bases__:
                    self._cx.enter_context(getattr(cls, "_init_machine")(self))

            # Initialize the shell
            self._cx.enter_context(self._init_shell())

            # Nothing went wrong during init, we can pop `self` from the stack
            # now to keep the machine active when entering the actual context.
            cx.pop_all()

        return self

    def __exit__(self, *args: typing.Any) -> None:
        self._cx.__exit__(*args)


class Initializer(Machine):
    @abc.abstractmethod
    def _init_machine(self) -> typing.ContextManager:
        raise NotImplementedError("abstract method")
