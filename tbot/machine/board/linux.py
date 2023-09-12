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
import time
import typing

import tbot
import tbot.error

from .. import board, channel, connector, machine


class LinuxStartupEvent(tbot.log.EventIO):
    def __init__(self, lnx: machine.Machine) -> None:
        self.lnx = lnx
        super().__init__(
            ["board", "linux", lnx.name],
            tbot.log.c("LINUX").bold + f" ({lnx.name})",
            verbosity=tbot.log.Verbosity.QUIET,
        )

        self.prefix = "   <> "
        self.verbosity = tbot.log.Verbosity.STDOUT

    def close(self) -> None:
        setattr(self.lnx, "bootlog", self.getvalue())
        self.data["output"] = self.getvalue()
        super().close()


class LinuxBoot(machine.Machine):
    _linux_init_event: typing.Optional[tbot.log.EventIO] = None

    def _linux_boot_event(self) -> tbot.log.EventIO:
        if self._linux_init_event is None:
            self._linux_init_event = LinuxStartupEvent(self)

        return self._linux_init_event


class LinuxBootLogin(machine.Initializer, LinuxBoot):
    """
    Machine :py:class:`~tbot.machine.Initializer` to wait for linux boot-up and
    automatically login.

    Use this initializer whenever you have a serial-console for a Linux system.

    **Example**:

    .. code-block:: python

        from tbot.machine import board, linux

        class StandaloneLinux(
            board.Connector,
            board.LinuxBootLogin,
            linux.Bash,
        ):
            # board.LinuxBootLogin config:
            username = "root"
            password = "hunter2"
    """

    login_prompt = "login: "
    """Prompt that indicates tbot should send the username."""

    login_delay = 0
    """
    The delay between first occurrence of login_prompt and actual login.

    This delay might be necessary if your system clutters the login prompt with
    log-messages during the first few seconds after boot.
    """

    password_prompt: channel.channel.ConvenientSearchString = "assword: "
    """Prompt that indicates tbot should send the password."""

    boot_timeout: typing.Optional[float] = None
    """
    Maximum time for Linux to reach the login prompt.

    The timer starts after initiation of the boot. This may either be power-on
    if booting into Linux directly or the point where the boot process is
    initiated from the bootloader (when using :py:class:`LinuxUbootConnector`).

    .. versionadded:: 0.10.0
    """

    # Used for timeout tracking
    _boot_start: typing.Optional[float] = None

    bootlog: str
    """Log of kernel-messages which were output during boot."""

    @property
    @abc.abstractmethod
    def username(self) -> str:
        """Username to login as."""
        pass

    @property
    @abc.abstractmethod
    def password(self) -> typing.Optional[str]:
        """Password to login with.  Set to ``None`` if no password is needed."""
        pass

    no_password_timeout: typing.Optional[float] = 5.0
    """
    Timeout after which login without a password should be attempted.  Set to
    ``None`` to disable this mechanism.

    .. versionadded:: 0.10.1
    """

    def _timeout_remaining(self) -> typing.Optional[float]:
        if self.boot_timeout is None:
            return None
        if self._boot_start is None:
            self._boot_start = time.monotonic()
        remaining = self.boot_timeout - (time.monotonic() - self._boot_start)
        if remaining <= 0:
            raise TimeoutError
        else:
            return remaining

    @contextlib.contextmanager
    def _init_machine(self) -> typing.Iterator:
        with contextlib.ExitStack() as cx:
            ev = cx.enter_context(self._linux_boot_event())
            cx.enter_context(self.ch.with_stream(ev))

            if self._boot_start is None:
                self._boot_start = time.monotonic()

            self.ch.read_until_prompt(
                prompt=self.login_prompt, timeout=self.boot_timeout
            )

            # On purpose do not login immediately as we may get some
            # console flooding from upper SW layers (and tbot's console
            # setup may get broken)
            if self.login_delay != 0:
                remaining = self._timeout_remaining()
                if remaining is not None and self.login_delay > remaining:
                    # we know that we will hit the timeout by waiting for
                    # login_delay so why not raise the TimeoutError now...
                    raise TimeoutError(
                        "login_delay would exceed boot_timeout, aborting."
                    )

                # Read everything while waiting for timeout to expire
                self.ch.read_until_timeout(self.login_delay)

                self.ch.sendline("")
                self.ch.read_until_prompt(
                    prompt=self.login_prompt, timeout=self._timeout_remaining()
                )

            self.ch.sendline(self.username)
            if self.password is not None:
                timeout = self._timeout_remaining()
                if self.no_password_timeout is not None:
                    if timeout is None:
                        timeout = self.no_password_timeout
                    else:
                        timeout = min(timeout, self.no_password_timeout)

                try:
                    self.ch.read_until_prompt(
                        prompt=self.password_prompt, timeout=timeout
                    )
                except TimeoutError:
                    # Call _timeout_remaining() to abort if the boot-timeout was reached
                    self._timeout_remaining()

                    # If we get here, the no_password_timeout expired and we
                    # should attempt continuing without a password.
                    tbot.log.warning(
                        "Didn't get asked for a password."
                        + "  Optimistically continuing without one..."
                    )
                else:
                    # No timeout exception means we're at the password prompt.
                    self.ch.sendline(self.password)

        yield None


class AskfirstInitializer(machine.Initializer, LinuxBoot):
    """
    Initializer to deal with ``askfirst`` TTYs.

    On some boards, the console is configured with ``askfirst`` which means that
    the getty for logging in is only spawned after an initial ENTER is sent.
    This initializer takes care of that by first waiting for the ``askfirst``
    prompt and then sending ENTER.

    The ``askfirst`` prompt can be customized with the ``askfirst_prompt`` attribute.

    **Example**:

    .. code-block:: python

        from tbot.machine import board, linux

        class StandaloneLinux(
            board.Connector,
            board.AskfirstInitializer,
            board.LinuxBootLogin,
            linux.Bash,
        ):
            # board.LinuxBootLogin config:
            username = "root"
            password = "hunter2"

    .. versionadded:: 0.10.6
    """

    askfirst_prompt = "Please press Enter to activate this console."
    """
    Prompt that indicates the board is waiting for ``askfirst`` confirmation.
    """

    # For proper integration with LinuxBootLogin
    boot_timeout: typing.Optional[float] = None
    _boot_start: typing.Optional[float] = None
    bootlog: str

    @contextlib.contextmanager
    def _init_machine(self) -> typing.Iterator:
        # This ExitStack holds the boot event until we successfully reached the
        # askfirst prompt.  Then it releases the boot event such that further
        # initializers like LinuxBootLogin can continue using it.
        with contextlib.ExitStack() as cx:
            ev = cx.enter_context(self._linux_boot_event())

            with self.ch.with_stream(ev):
                if self._boot_start is None:
                    self._boot_start = time.monotonic()

                # Using expect() instead of read_until_prompt() so we are not
                # confused by garbage following the prompt.
                self.ch.expect(self.askfirst_prompt, timeout=self.boot_timeout)
                self.ch.sendline("")

            cx.pop_all()

        yield None


Self = typing.TypeVar("Self", bound="LinuxUbootConnector")


class LinuxUbootConnector(connector.Connector, LinuxBootLogin, board.BoardMachineBase):
    """
    Connector for booting Linux from U-Boot.

    This connector can either boot from a :py:class:`~tbot.machine.board.Board`
    instance or from a :py:class:`~tbot.machine.board.UBootShell` instance.  If
    booting directly from the board, it will first initialize a U-Boot machine
    and then use it to kick off the boot to Linux.  See above for an example.
    """

    @property
    @abc.abstractmethod
    def uboot(self) -> typing.Type[board.UBootShell]:
        """
        U-Boot machine to use when booting directly from a
        :py:class:`~tbot.machine.board.Board` instance.
        """
        raise tbot.error.AbstractMethodError()

    def do_boot(self, ub: board.UBootShell) -> channel.Channel:
        """
        Boot procedure.

        An implementation of this method should use the U-Boot machine given as
        ``ub`` to kick off the Linux boot.  It should return the channel to the
        now booting Linux.  This will in almost all cases be achieved by using
        the :py:meth:`tbot.machine.board.UBootShell.boot` method.

        **Example**:

        .. code-block:: python

            from tbot.machine import board, linux

            class LinuxFromUBoot(
                board.LinuxUbootConnector,
                board.LinuxBootLogin,
                linux.Bash,
            ):
                uboot = MyUBoot  # <- Our UBoot machine

                def do_boot(self, ub):  # <- Procedure to boot Linux
                   # Any logic necessary to prepare for boot
                   ub.env("autoload", "false")
                   ub.exec0("dhcp")

                   # Return the channel using ub.boot()
                   return ub.boot("run", "nfsboot")

                ...
        """
        return ub.boot("boot")

    def __init__(self, b: typing.Union[board.Board, board.UBootShell]) -> None:
        self._b = b

    @classmethod
    @contextlib.contextmanager
    def from_context(
        cls: typing.Type[Self], ctx: "tbot.Context"
    ) -> typing.Iterator[Self]:
        with contextlib.ExitStack() as cx:
            ub = cx.enter_context(ctx.request(tbot.role.BoardUBoot, exclusive=True))
            m = cx.enter_context(cls(ub))  # type: ignore
            yield typing.cast(Self, m)

    @contextlib.contextmanager
    def _connect(self) -> typing.Iterator[channel.Channel]:
        with contextlib.ExitStack() as cx:
            if isinstance(self._b, board.Board):
                ub = cx.enter_context(self.uboot(self._b))  # type: ignore
            elif isinstance(self._b, board.UBootShell):
                ub = cx.enter_context(self._b)
            else:
                raise TypeError(f"Got {self._b!r} instead of Board/U-Boot machine")

            self._linux_boot_event()

            yield self.do_boot(ub).take()

    def clone(self: Self) -> Self:
        """This machine cannot be cloned."""
        raise NotImplementedError("can't clone Linux_U-Boot Machine")

    @property
    def board(self) -> board.Board:
        if isinstance(self._b, board.Board):
            return self._b
        elif isinstance(self._b, board.UBootShell):
            try:
                return getattr(self._b, "board")  # type: ignore
            except AttributeError:
                raise Exception("U-Boot machine does not reference a board machine!")
