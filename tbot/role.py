import contextlib
import types
from typing import Any, Iterator

import tbot
from tbot.machine import board, linux


class Role:
    """
    Base class for all roles.

    See :ref:`tbot_role` for details.
    """

    pass


class LabHost(linux.Lab, Role):
    """
    Role for the "lab-host".

    As shown on the diagram above, the lab-host is the
    central host from where connections to other machines are made.  This can
    be your localhost in simple cases or any ssh-reachable machine if working
    remotely.

    A machine for this role should be registered by the lab-config.  If this is
    not done, it defaults to a localhost lab-host machine.

    Testcases should use the lab-host for any "host" operations if that is at
    all possible.
    """

    pass


class BuildHost(linux.Builder, Role):
    """
    Role for the "build-host".

    The build-host is an optional machine for building/compiling software.  In
    simple cases, this can just be the lab-host but when builds are more
    complex, it can be beneficial to use an external build-server with more
    CPU-power for this.

    Generic testcases for building e.g. U-Boot or Linux should use this machine.
    """

    pass


class LocalHost(linux.LinuxShell, Role):
    """
    Role for the localhost or "tbot-host", the machine tbot is running on.

    When using a remote lab-host, sometimes on wants to e.g. download an
    artifact from the lab-host to the localhost or upload a local file to the
    lab-host.  This machine can be referenced for such purposes.

    In most circumstances, it should not be necessary to register a custom
    machine for this role.  It might however be useful for situations where you
    want to e.g. modify the ``workdir()`` on localhost.
    """

    pass


class Board(board.Board, Role):
    """
    Role for the DUT (device under test, "the board") hardware.

    In tbot, the board is represented by one machine for the "physical device"
    and separate machines for the software running on it.  This role defines
    the physical hardware and e.g. manages turning on and off board power.

    See :ref:`config-board` for more.
    """

    pass


class BoardUBoot(board.UBootShell, Role):
    """
    Role for a U-Boot bootloader machine running on the :py:class:`tbot.role.Board`.

    See :ref:`config-board-uboot` for details how such a machine should be configured.
    """

    pass


class BoardLinux(linux.LinuxShell, Role):
    """
    Role for a Linux OS running on the :py:class:`tbot.role.Board`.

    There's multiple ways to configure such a machine.  See
    :ref:`config-board-linux`.
    """

    pass


def isrole(cls: Any) -> bool:
    try:
        return Role in getattr(cls, "__bases__")
    except AttributeError:
        raise ValueError("{cls!r} is not a class") from None


def rolename(cls: Any) -> str:
    return f"<{cls.__module__}.{cls.__qualname__}>"


# This function will be called when creating a context and should register
# a few default machines for certain roles.  Any registration here **must**
# use weak=True!
def _register_default_machines(ctx: "tbot.Context") -> None:
    # Use the 'LocalLabHost' from the selectable module as a default lab- and
    # local-host for now.
    from tbot.selectable import LocalLabHost

    ctx.register(LocalLabHost, [LabHost, LocalHost], weak=True)

    # We need to provide a build-host that maps to the actual build-host
    # defined by the legacy build() method on the lab-host.
    class BuildHostProxy:
        @classmethod
        @contextlib.contextmanager
        def from_context(cls, ctx: tbot.Context) -> Iterator:
            with contextlib.ExitStack() as cx:
                lh = cx.enter_context(ctx.request(LabHost))
                with lh.build() as bh:
                    # It's a common bug that people just return `self` from
                    # lh.build().  Detect this and manually create a bh clone:
                    if bh is lh:
                        tbot.log.warning(
                            """\
The build() method for the selected lab should not return `self` but instead `self.clone()`.
    Attempting to call build_host.clone() automatically now ..."""
                        )
                        bh = cx.enter_context(bh.clone())

                    # Do a dirty trick to make `bh` actually a ProxyBuildHost
                    # so the Context doesn't get alarmed by us returning an
                    # instance of the wrong type.
                    wrapper_class = types.new_class(
                        "BuildHostProxy", (bh.__class__, BuildHostProxy)
                    )
                    bh.__class__ = wrapper_class

                    yield bh

    ctx.register(BuildHostProxy, [BuildHost], weak=True)  # type: ignore
