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
import tbot.error
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
        raise tbot.error.AbstractMethodError()

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
