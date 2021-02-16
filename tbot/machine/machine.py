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
import contextlib
import re
import typing
import tbot.error
from . import channel

Self = typing.TypeVar("Self", bound="Machine")

_first_cap_re = re.compile("(.)([A-Z][a-z]+)")
_all_cap_re = re.compile("([a-z0-9])([A-Z])")


class Machine(abc.ABC):
    """
    Base class for all machines.

    This class contains the necessary code to compose the different parts of a
    machine into a usable class.  You won't need to use it directly in most
    cases as :py:class:`~tbot.machine.connector.Connector` and
    :py:class:`~tbot.machine.shell.Shell` both inherit from it.
    """

    __slots__ = ("_cx", "_rc", "ch")

    ch: channel.Channel
    """
    Channel to communicate with this machine.

    .. warning::

        Please refrain from interacting with the channel directly.  Instead,
        write a :py:class:`~tbot.machine.shell.Shell` that wraps around the
        channel interaction.  That way, the state of the channel is only
        managed in a single place and you won't have to deal with nasty bugs
        when multiple parties make assumptions about the state of the channel.
    """

    @property
    def name(self) -> str:
        """
        Name of this machine.

        By default, the name is derived from the class-name but you might want
        to customize it.
        """
        # by default, try to kebab-case the class name
        s1 = _first_cap_re.sub(r"\1-\2", self.__class__.__name__)
        return _all_cap_re.sub(r"\1-\2", s1).lower()

    # Abstract methods that will be implemented by connector and shell
    @abc.abstractmethod
    def _connect(self) -> typing.ContextManager[channel.Channel]:
        raise tbot.error.AbstractMethodError()

    @classmethod
    @abc.abstractmethod
    def from_context(
        cls: typing.Type[Self], ctx: "tbot.Context"
    ) -> typing.ContextManager[Self]:
        raise tbot.error.AbstractMethodError()

    @abc.abstractmethod
    def clone(self: Self) -> Self:
        raise tbot.error.AbstractMethodError()

    @abc.abstractmethod
    def _init_shell(self) -> typing.ContextManager:
        raise tbot.error.AbstractMethodError()

    def init(self) -> None:
        """
        An optional hook that allows running some code after the machine is initialized.

        **Example**:

        .. code-block:: python

            class FooUBoot(board.Connector, board.UBootShell):
                name = "foo-u-boot"
                prompt = "=> "

                def init(self):
                    self.env("autoload", "no")
                    self.exec0("dhcp")

                    self.env("serverip", "192.168.1.2")
        """
        pass

    _orig: "typing.Optional[Machine]" = None
    """
    The "original" machine if this is a clone.  If ``_orig`` is ``None``, it is
    assumed that ``self`` is the original and ``_orig`` may be set to ``self``.
    It is also ok for your code to set ``_orig`` to ``self`` explicitly.
    """

    def __eq__(self, other: object) -> bool:
        """
        Two machines are 'equal' if they are clones.
        """
        if not isinstance(other, Machine):
            return NotImplemented

        if self._orig is None:
            self._orig = self

        if other._orig is None:
            other._orig = other

        return self._orig is other._orig

    def __hash__(self) -> int:
        """
        Cloned machines should get the same hash value.
        """
        if self._orig is None:
            self._orig = self

        return hash(id(self._orig))

    def __enter__(self: Self) -> Self:
        self._rc = getattr(self, "_rc", 0)
        self._rc += 1

        if self._rc > 1:
            return self

        self._cx = contextlib.ExitStack().__enter__()

        # This inner stack is meant to protect the __enter__() implementations
        with contextlib.ExitStack() as cx:
            # If anything goes wrong, execute this machine's __exit__()
            cx.push(self)

            # Run pre-connection init, if specified
            for cls in type(self).mro():
                if PreConnectInitializer in cls.__bases__:
                    self._cx.enter_context(getattr(cls, "_init_pre_connect")(self))

            # Run the connector
            self.ch = self._cx.enter_context(self._connect())

            # Run all initializers according to the MRO
            for cls in type(self).mro():
                if Initializer in cls.__bases__:
                    self._cx.enter_context(getattr(cls, "_init_machine")(self))

            # Initialize the shell
            self._cx.enter_context(self._init_shell())

            # Run post-shell init, if specified
            for cls in type(self).mro():
                if PostShellInitializer in cls.__bases__:
                    self._cx.enter_context(getattr(cls, "_init_post_shell")(self))

            # Run optional custom initialization code
            self.init()

            # Nothing went wrong during init, we can pop `self` from the stack
            # now to keep the machine active when entering the actual context.
            cx.pop_all()

        return self

    def __exit__(self, *args: typing.Any) -> None:
        self._rc -= 1

        if self._rc == 0:
            self._cx.__exit__(*args)


class Initializer(Machine):
    """
    Base-class for machine initializers.
    """

    @abc.abstractmethod
    def _init_machine(self) -> typing.ContextManager:
        """
        Run this initializer.

        Implementations of this method can make use of ``self.ch`` as they will
        run after the connector has succeeded.

        .. todo::

            More docs for this ...
        """
        raise tbot.error.AbstractMethodError()


class PreConnectInitializer(Machine):
    """
    Base-class for pre-connection initializer context.

    This initializer is run  before connecting to the machine, before
    :py:meth:`tbot.machine.Initializer._init_machine`
    """

    @abc.abstractmethod
    def _init_pre_connect(self) -> typing.ContextManager:
        """
        Pre-connection initialization context.
        """
        raise tbot.error.AbstractMethodError()


class PostShellInitializer(Machine):
    """
    Base-class for post-shell initializer context.

    This initializer is run after :py:meth:`tbot.machine.Initializer._init_machine`
    and after the shell has been initialized.
    """

    @abc.abstractmethod
    def _init_post_shell(self) -> typing.ContextManager:
        """
        Post-shell initialization context.
        """
        raise tbot.error.AbstractMethodError()
