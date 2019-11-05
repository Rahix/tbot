import abc
import typing
from .. import channel, machine

Self = typing.TypeVar("Self", bound="Connector")


class Connector(machine.Machine):
    """
    Base-class for machine connectors.
    """

    __slots__ = ()

    @abc.abstractmethod
    def _connect(self) -> typing.ContextManager[channel.Channel]:
        """
        Establish the channel.

        This method will be called during machine-initialization and should
        yield a channel which will then be used for the machine.

        This method's return type is annotated as
        ``typing.ContextManager[channel.Channel]``, to allow more complex setup
        & teardown.  As channels implement the context-manager protocol, simple
        connectors can just return the channel.  A more complex connector can
        use the following pattern:

        .. code-block:: python

            import contextlib

            class MyConnector(Connector):
                @contextlib.contextmanager
                def _connext(self) -> typing.Iterator[channel.Channel]:
                    try:
                        # Do setup
                        ...
                        yield ch
                    finally:
                        # Do teardown
                        ...
        """
        raise NotImplementedError("abstract method")

    @abc.abstractmethod
    def clone(self: Self) -> Self:
        """
        Create a duplicate of this machine.

        For a lot of connections, it is trivial to open a second one in
        parallel.  This can be exploited to easily connect further from one
        host to the next, thus building a tunnel.

        On the other hand, a serial connection to a board is unique and can't
        be cloned.  Such connectors should raise an exception is ``.clone()``
        is called.
        """
        raise NotImplementedError("abstract method")
