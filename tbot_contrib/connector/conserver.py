import abc
import typing
from tbot.machine import channel, connector, linux

__all__ = ("ConserverConnector",)


class ConserverConnector(connector.ConsoleConnector):
    """
    Connect to a serial console using `conserver`_.

    You can configure the device name using the ``conserver_device`` property.

    **Example**: (board config)

    .. code-block:: python

        from tbot.machine import board
        from tbot_contrib.connector import conserver

        class MyBoard(conserver.ConserverConnector, board.Board):
            conserver_device = "ttyS0"

        BOARD = MyBoard
    """

    @property
    @abc.abstractmethod
    def conserver_device(self) -> str:
        """
        Device name for conserver.

        This property is **required**.
        """
        raise Exception("abstract method")

    conserver_master: typing.Optional[str] = None
    """Optional name of the conserver master to connect to (``-M``)."""

    conserver_command: typing.Union[str, typing.List] = "console"
    """
    Command to connect with conserver.

    Can be either a :py:class:`str` (single command name) or a :py:class:`list`
    (with added command-line args).  For example:

    .. code-block:: python

        conserver_command = ["console", "-p1234", "-n"]
    """

    conserver_forcerw: bool = True
    """
    Whether to force the console into read-write mode (``-f``).

    This is necessary for the case where a session is already attached to this
    console while tbot is running.  Otherwise, tbot will not be able to
    properly intercept the boot process and might fail for odd reasons.

    If you don't want tbot to mess with an already running session, set this to
    ``False``.
    """

    def connect(self, mach: linux.LinuxShell) -> channel.Channel:
        if isinstance(self.conserver_command, str):
            command = [self.conserver_command]
        else:
            command = self.conserver_command

        args = []
        if self.conserver_forcerw:
            args.append("-f")

        if self.conserver_master is not None:
            args.append(f"-M{self.conserver_master}")

        ch = mach.open_channel(*command, *args, self.conserver_device)
        return ch
