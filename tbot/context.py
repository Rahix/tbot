import contextlib
import typing
from typing import Any, Callable, Dict, Iterator, List, Set, Type, TypeVar, Union

import tbot
import tbot.error
import tbot.role
from tbot import machine

M = TypeVar("M", bound=machine.Machine)


class Context(typing.ContextManager):
    """
    A context which machines can be registered in and where instances can be retrieved from.

    You will usually access the global context :py:data:`tbot.ctx` which is an
    instance of this class instead of instanciating :py:class:`tbot.Context`
    yourself.  See the :ref:`context` guide for a detailed introduction.
    """

    def __init__(self, *, add_defaults: bool = False) -> None:
        self._roles: Dict[Type[tbot.role.Role], Type[machine.Machine]] = {}
        self._weak_roles: Set[Type[tbot.role.Role]] = set()
        self._instances: Dict[Type[machine.Machine], machine.Machine] = {}
        self._open_contexts = 0

        if add_defaults:
            tbot.role._register_default_machines(self)

    def register(
        self, machine: Type[M], roles: Union[Any, List[Any]], *, weak: bool = False
    ) -> None:
        """
        Register a machine in this context for certain roles.

        Registers the machine-class ``machine`` for the role ``roles`` or, if
        ``roles`` is a list, for all roles it contains.  If for any role
        a machine is already registered, an exception is thrown.

        This function is usually called in the ``register_machines()`` function
        of a lab- or board-config:

        .. code-block:: python

            class SomeLabHostClass(...):
                ...

            def register_machines(ctx: tbot.Context) -> None:
                ctx.register(SomeLabHostClass, tbot.role.LabHost)

                # or, to register for multiple roles
                ctx.register(SomeLabHostClass, [tbot.role.LabHost, tbot.role.BuildHost])

        :param machine: A concrete machine-class to be registered.  This
            machine-class will later be instanciated on request via its
            :py:meth:`Connector.from_context()
            <tbot.machine.connector.Connector.from_context()>` classmethod.
        :param roles: Either a single role or a list of roles for which
            ``machine`` should be registered.
        :param bool weak: Changes the way registration works:  The machine is
            only registered for those roles which do not already have a machine
            registered.  It will be registered as a weak default which means
            a later register will overwrite it without erroring.  This is
            usually not necessary and should be used with care.
        """
        if not isinstance(roles, list):
            roles = [roles]

        for role in roles:
            if not issubclass(role, tbot.role.Role):
                tbot.error.TbotException(f"{role!r} is not a role")

            if role in self._roles:
                if weak:
                    continue
                elif role in self._weak_roles:
                    # Overwrite the weak default
                    self._weak_roles.discard(role)
                else:
                    raise KeyError(
                        f"a machine is already registered for role {tbot.role.rolename(role)}"
                    )

            if weak:
                self._weak_roles.add(role)
            self._roles[role] = machine

    @contextlib.contextmanager
    def request(self, type: Callable[..., M]) -> Iterator[M]:
        """
        Request a machine instance from this context.

        Requests an instance of the :ref:`role <tbot_role>` ``type`` from the context.  If no
        instance exists, one will be created.  If a previous testcase has
        already requested such an instance, the same instance is returned.

        This function must be used as a context manager:

        .. code-block:: python

            @tbot.testcase
            def foo_bar():
                with tbot.ctx.request(tbot.role.LabHost) as lh:
                    lh.exec0("uname", "-a")

        Alternatively, if you need multiple machines, a pattern similar to
        :py:class:`contextlib.ExitStack` can be used:

        .. code-block:: python

            @tbot.testcase
            def foo_bar():
                with tbot.ctx() as cx:
                    lh = cx.request(tbot.role.LabHost)
                    bh = cx.request(tbot.role.BuildHost)

                    lh.exec0("cat", "/etc/os-release")
                    bh.exec0("free", "-h")

        :param type: The :ref:`role <tbot_role>` for which a machine instance
            is requested.
        """
        type = typing.cast(Type[M], type)

        m = None

        try:
            with contextlib.ExitStack() as cx:
                if type not in self._roles and type in self._instances:
                    m = cx.enter_context(self._instances[type])
                elif type in self._roles:
                    machine_class = self._roles[type]

                    if machine_class in self._instances:
                        m = cx.enter_context(self._instances[machine_class])
                    else:
                        m = cx.enter_context(machine_class.from_context(self))
                        assert isinstance(m, machine_class), f"machine type mismatch"
                        self._instances[machine_class] = m
                else:
                    raise IndexError(f"no machine found for {type!r}")

                yield typing.cast(M, m)
        finally:
            # After exiting the context, check if this machine has a refcount
            # of 0.  This would mean it was deinitialized and we should discard
            # it now.
            if m is not None and m._rc == 0:
                del self._instances[machine_class]

    @contextlib.contextmanager
    def __call__(self) -> "Iterator[ContextHandle]":
        with contextlib.ExitStack() as exitstack:
            handle = ContextHandle(self, exitstack)
            yield handle

    def __enter__(self) -> "Context":
        self._open_contexts += 1
        return self

    def __exit__(self, *args: Any) -> None:
        self._open_contexts -= 1

        if self._open_contexts == 0:
            for inst in self._instances:
                tbot.log.warning("Found a dangling {inst!r} in this context")


class ContextHandle:
    def __init__(self, ctx: Context, exitstack: contextlib.ExitStack) -> None:
        self.ctx = ctx
        self._exitstack = exitstack

    def request(self, type: Callable[..., M]) -> M:
        return self._exitstack.enter_context(self.ctx.request(type))
