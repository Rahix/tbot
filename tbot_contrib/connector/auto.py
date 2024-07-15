import abc
import contextlib
from dataclasses import dataclass
from typing import ContextManager, Iterator, Optional, Union

import tbot
from tbot.machine import channel, connector, linux
from tbot.tc.shell import check_for_tool


@dataclass
class TeOptions:
    machine: linux.LinuxShell
    baudrate: int
    serial_port: Union[str, linux.Path]


class TerminalEmulator(abc.ABC):
    tool_name: Optional[str] = None

    @classmethod
    def check_available(cls, host: linux.LinuxShell) -> bool:
        if cls.tool_name is None:
            raise NotImplementedError(f"check_available not implemented for {cls!r}")
        return check_for_tool(host, cls.tool_name)

    @classmethod
    @abc.abstractmethod
    def connect(cls, opt: TeOptions) -> ContextManager[channel.Channel]:
        raise tbot.error.AbstractMethodError()


class Tio(TerminalEmulator):
    tool_name = "tio"

    @classmethod
    @contextlib.contextmanager
    def connect(cls, opt: TeOptions) -> Iterator[channel.Channel]:
        ch = opt.machine.open_channel(
            cls.tool_name, "-b", str(opt.baudrate), opt.serial_port
        )
        try:
            yield ch
        finally:
            if not ch.closed:
                ch.sendcontrol("T")
                ch.send("q")


class Picocom(TerminalEmulator):
    tool_name = "picocom"

    @classmethod
    @contextlib.contextmanager
    def connect(cls, opt: TeOptions) -> Iterator[channel.Channel]:
        ch = opt.machine.open_channel(
            cls.tool_name, "-q", "-b", str(opt.baudrate), opt.serial_port
        )
        try:
            yield ch
        finally:
            if not ch.closed:
                ch.sendcontrol("A")
                ch.sendcontrol("Q")


class AutoConsoleConnector(connector.ConsoleConnector):
    """
    Console connector that automatically chooses an available terminal emulator
    to connect to a local console device.

    **Example**:

    .. code-block:: python

        from tbot_contrib.connector.auto import AutoConsoleConnector
        from tbot.machine import board

        class FooBoard(AutoConsoleConnector, board.Board):
            serial_port = "/dev/ttyUSB0"
            baudrate = 115200

    .. versionadded:: 0.10.3
    """

    @property
    @abc.abstractmethod
    def serial_port(self) -> Union[str, linux.Path]:
        """Serial port to connect to."""
        raise tbot.error.AbstractMethodError()

    baudrate = 115200
    """
    Baudrate of the serial line.
    """

    tools = [Tio, Picocom]
    """
    List of terminal emulators which may be used to connect.

    It is best the leave this list complete so tbot can automatically figure
    out which tool is available and use that one.
    """

    @contextlib.contextmanager
    def connect(self, mach: linux.LinuxShell) -> Iterator[channel.Channel]:
        options = TeOptions(
            machine=mach,
            baudrate=self.baudrate,
            serial_port=self.serial_port,
        )

        for tool in self.tools:
            if tool.check_available(mach):
                with tool.connect(options) as ch:
                    yield ch
                    return
                break

        tool_names = [
            tool.tool_name for tool in self.tools if tool.tool_name is not None
        ]
        raise tbot.error.TbotException(
            f"""\
No compatible terminal emulator program was found on host {mach.name!r}!

Please install one of the following tools: {', '.join(tool_names)}"""
        )
