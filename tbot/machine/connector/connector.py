# tbot, Embedded Automation Tool
# Copyright (C) 2019  Harald Seiler
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import abc
import typing

import tbot
import tbot.error
from .. import channel, machine

Self = typing.TypeVar("Self", bound="Connector")


class Connector(machine.Machine):
    """
    Base-class for machine connectors.
    """

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
                def _connect(self) -> typing.Iterator[channel.Channel]:
                    try:
                        # Do setup
                        ...
                        yield ch
                    finally:
                        # Do teardown
                        ...
        """
        raise tbot.error.AbstractMethodError()

    @classmethod
    def from_context(
        cls: typing.Type[Self], ctx: "tbot.Context"
    ) -> typing.ContextManager[Self]:
        """
        Create this machine from a tbot context.

        This method defines how tbot can automatically attempt creating this
        machine from a given context. It is usually defined by the connector
        but might be overridden by board config in certain more complex
        scenarios.

        This method must return a context-manager that, upon entering, yields a
        **fully initialized** machine. In practical terms this means, the
        implementation must enter the "machine's context" as well. As an
        example, the most basic implementation would look like this:

        .. code-block:: python

            @contextlib.contextmanager
            def from_context(cls, ctx):
                # Create instance and enter its context, in this example, no
                # args are passed to the constructor ...
                with cls() as m:
                    yield m
        """
        raise NotImplementedError(
            f"connector of {cls!r} does not (yet) implement from_context()"
        )

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

        .. note::

            **Important**: You should **always** set the new machines ``_orig``
            attribute to the original machine (either ``self._orig`` or, if
            that is ``None``, ``self``) so tbot knows these machines belong
            together!  The common pattern is:

            .. code-block:: python

                def clone(self):
                    new = ...
                    new._orig = self._orig or self
                    return new

            Not setting ``_orig`` means that tbot will treat the new and old
            instances as separate machines which (theoretically) can't interact
            with each other.
        """
        raise tbot.error.AbstractMethodError()
