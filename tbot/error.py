# tbot, Embedded Automation Tool
# Copyright (C) 2020  Harald Seiler
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
import inspect
import typing
from typing import Any, Optional

if typing.TYPE_CHECKING:
    from tbot import machine


class TbotException(Exception):
    """
    Base-class for all exceptions which are specific to tbot.
    """


class ApiViolationError(TbotException, RuntimeError):
    """
    Base-class for all exceptions that are raised due to wrong use of tbot's API.

    Seeing this exception means that the calling code has a bug and needs to be
    fixed. This is in contrast to :py:class:`tbot.error.MachineError` which is
    the base-class for exceptions raised due to unexpected occurrences on the
    remote side during a test-run.

    The subclasses of ``ApiViolationError`` should detail in their
    documentation how to fix them.

    .. versionadded:: 0.10.2
    """


class MachineError(TbotException):
    """
    Base-class for exceptions raised due to remote machine errors.

    Usually, this indicates something is wrong with the remote systems that
    tbot was interacting with.  This is in contrast to
    :py:class:`tbot.error.ApiViolationError` which is raised when downstream
    code has a bug and/or misuses the tbot API.

    .. versionadded:: 0.10.2
    """


class AbstractMethodError(ApiViolationError, NotImplementedError):
    """
    A method which needs to be overwritten was called from code.  This
    shouldn't ever really happen in practice hopefully ...
    """

    def __init__(self, method: Optional[str] = None) -> None:
        if method is None:
            # Grab the method name of the calling frame
            calling_frame = inspect.stack()[1]
            self.method = calling_frame.function
        else:
            self.method = method

        super().__init__(
            f"Called abstract method {self.method!r}.  This is probably an incorrect call to super()."
        )


class WrongHostError(ApiViolationError, ValueError):
    """
    A method was called with arguments that reference a different host.
    """

    def __init__(self, arg: Any, host: "machine.Machine") -> None:
        self.arg = arg
        self.host = host

        super().__init__(f"{arg!r} references a host/machine that is not {host!r}")


class ContextError(ApiViolationError, RuntimeError):
    """
    A forbidden or wrong kind of interaction with tbot's context was attempted.

    The exception message will include more details.  As an example, this
    exception is raised when requesting an instance that is currently
    exclusively requested elsewhere.

    .. versionadded:: 0.10.2
    """


class MachineNotFoundError(ApiViolationError, IndexError):
    """
    The requested machine was not found in the tbot context.

    The most likely cause for this is that the selected configuration did not
    register a machine for the requested role.

    .. versionadded:: 0.10.2
    """


_repr = repr


class CommandFailure(MachineError):
    """
    A command exited with non-zero exit code.

    This exception is raised by ``exec0()`` methods to indicate command failures.

    .. versionadded:: 0.10.2
    """

    host: "machine.Machine"
    """
    The host where the failed command was executed.

    This host may or may not be available at the time of catching the exception,
    depending on how far the exception was bubbled up.
    """

    cmd: Any
    """
    The original form of the command, usually a list of arguments.

    For a readable and displayable version, use the ``repr`` field instead.
    """

    repr: str
    """
    String representation of the command which failed.

    Should only be used for diagnostic purposes.
    """

    def __init__(
        self, host: "machine.Machine", cmd: Any, *, repr: Optional[str] = None
    ) -> None:
        self.host = host
        self.cmd = cmd
        if repr is not None:
            self.cmd_repr = repr
        else:
            self.cmd_repr = _repr(self.cmd)

        super().__init__(f"command failed: [{self.host.name}] {self.cmd_repr}")


class ChannelClosedError(MachineError):
    """
    Error type for exceptions when a channel was closed unexpectedly.

    This error is raised when interaction with a channel is attemped which was
    either closed explicitly beforehand or which was closed unexpectedly by the
    remote end.

    .. versionadded:: 0.10.2
    """


class UncleanShellError(MachineError):
    """
    While trying to prepare the remote shell, tbot detected unexpected behavior.

    This error means that the shell responded with unexpected output during
    setup.  tbot cannot proceed to interact, as it cannot be certain about the
    state of the remote shell.

    If you encounter this error, enable verbose channel logging to see what
    unexpected output was received.  You need to ensure that the remote system
    does not send this additional output.

    .. versionadded:: UNRELEASED
    """

    def __init__(
        self,
        host: "machine.Machine",
    ) -> None:
        self.host = host
        super().__init__(
            f"detected unclean shell for {host.name!r}, cannot interact safely"
        )


class InvalidRetcodeError(MachineError):
    """
    While trying to fetch the return code of a command, unexpected output was received.

    This error usually indicates some deeper issue with the machine connection.
    For example, there could be kernel log messages being printed in between
    command output.

    .. versionadded:: 0.10.7
    """

    def __init__(
        self,
        host: "machine.Machine",
        retcode_str: str,
    ) -> None:
        self.host = host
        self.retcode_str = retcode_str
        super().__init__(
            f"received string {retcode_str!r} instead of a return code integer"
        )


class MissingToolError(MachineError):
    """
    A tool that is needed for a testcase is not installed on the respective machine.

    The usual solution is to install one of the listed tools.

    .. versionadded:: UNRELEASED
    """

    def __init__(
        self,
        host: "machine.Machine",
        need_one_of: typing.List[str],
        message: typing.Optional[str] = None,
    ):
        self.host = host
        self.message = message
        self.need_one_of = need_one_of
        tools_list = ", ".join(f"`{t}`" for t in self.need_one_of)
        msg = message + "\n" if message is not None else ""
        super().__init__(
            f"{msg}one of the following tools is needed on {host.name!r}: {tools_list}"
        )


class ChannelBorrowedError(ApiViolationError):
    """
    Error type for exceptions when accessing a channel which is currently borrowed.

    This error will be raised when an attempt is made to interact with a
    channel which is currently borrowed.  As an example, when an interactive
    command is started with :py:meth:`LinuxShell.run`, while this command is
    running, the channel of the ``LinuxShell`` is borrowed and cannot be used.
    So a call to, for example, ``exec0()`` during this time would raise
    ``ChannelBorrowedError``.

    .. versionadded:: 0.10.2
    """

    def __init__(self) -> None:
        super().__init__("channel is currently borrowed by another machine")


class ChannelTakenError(ApiViolationError):
    """
    Error type for exceptions when accessing a channel which was "taken".

    This error will be raised when an attempt is made to interact with a
    channel which is was "taken".  The channel docs contain more details about
    this concept.  Essentially, a different machine now uses the channel so it
    can no longer be accessed from its previous "owner".

    .. versionadded:: 0.10.2
    """

    def __init__(self) -> None:
        super().__init__(
            "channel was taken by another machine."
            + " it can no longer be accessed from here"
        )


class IllegalDataException(ApiViolationError):
    """
    Raised when attempting to write illegal data to a channel.

    Some channels cannot deal with all byte sequences.  For example, certain
    escape sequences will mess up the connection.  If an attempt is made to
    send such data, this exception is raised.  The exact set of illegal
    sequences depends on the specific machine configuration.

    In most situations, the shell implementation will escape such data
    correctly.  This error should only become relevant when directly
    interacting with a channel.

    .. versionadded:: 0.10.2
    """


class UnboundedPatternError(ApiViolationError, ValueError):
    """
    Raised when a regex pattern is used which does not have a bounded length.

    tbot requires the use of patterns with a bounded length to keep track of
    incoming data efficiently.  A bounded pattern is one which does not use any
    infinitely repeating expressions.

    For example, ``r".*"`` is unbounded, but ``r".{0,80}"`` is.

    .. versionadded:: UNRELEASED
    """

    def __init__(self, pattern: bytes) -> None:
        self.pattern = pattern

        super().__init__(f"Regex expression {pattern!r} is not bounded")
