import abc
import contextlib
import io
import typing

import tbot
from .. import machine, board, channel, connector


class LinuxBoot(machine.Machine):
    _linux_init_event: typing.Optional[tbot.log.EventIO] = None

    def _linux_boot_event(self) -> tbot.log.EventIO:
        if self._linux_init_event is None:
            self._linux_init_event = tbot.log.EventIO(
                ["board", "linux", self.name],
                tbot.log.c("LINUX").bold + f" ({self.name})",
                verbosity=tbot.log.Verbosity.QUIET,
            )

            self._linux_init_event.prefix = "   <> "
            self._linux_init_event.verbosity = tbot.log.Verbosity.STDOUT

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
    The delay between first occurence of login_prompt and actual login.

    This delay might be necessary if your system clutters the login prompt with
    log-messages during the first few seconds after boot.
    """

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

    @contextlib.contextmanager
    def _init_machine(self) -> typing.Iterator:
        bootlog_stream = io.StringIO()
        with contextlib.ExitStack() as cx:
            ev = cx.enter_context(self._linux_boot_event())
            cx.enter_context(self.ch.with_stream(ev))
            cx.enter_context(self.ch.with_stream(bootlog_stream))

            self.ch.read_until_prompt(prompt=self.login_prompt)

            # On purpose do not login immediately as we may get some
            # console flooding from upper SW layers (and tbot's console
            # setup may get broken)
            if self.login_delay != 0:
                try:
                    self.ch.read(timeout=self.login_delay)
                except TimeoutError:
                    pass
                self.ch.sendline("")
                self.ch.read_until_prompt(prompt=self.login_prompt)

            self.ch.sendline(self.username)
            if self.password is not None:
                self.ch.read_until_prompt(prompt="assword: ")
                self.ch.sendline(self.password)

        self.bootlog = bootlog_stream.getvalue()
        bootlog_stream.close()
        yield None


Self = typing.TypeVar("Self", bound="LinuxUbootConnector")


class LinuxUbootConnector(connector.Connector, LinuxBootLogin):
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
        raise NotImplementedError("abstract method")

    def do_boot(self, ub: board.UBootShell) -> channel.Channel:
        """
        Boot procedure.

        An implementation of this method should use the U-Boot machine given as
        ``ub`` to kick off the Linux boot.  It should return the channel to the
        now booting Linux.  This will in almost all cases be archieved by using
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

                def do_boot(ub):  # <- Procedure to boot Linux
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
