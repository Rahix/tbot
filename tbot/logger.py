"""
Logger
------
"""
import abc
import time
import json
import pathlib
import enum
import typing
import sys

def has_unicode(with_unicode: str, without_unicode: str) -> str:
    """
    Check whether the terminal supports unicode, if it does,
    returns the ``with_unicode`` string, if it doesn't, returns
    the ``without_unicode`` string.

    :param with_unicode: String to be returned, if the terminal does
                         support unicode
    :type with_unicode: str
    :param without_unicode: String to be returned, if the terminal does
                            not support unicode
    :type without_unicode: str
    :rtype: str
    """
    if sys.stdout.encoding == "UTF-8":
        return with_unicode
    return without_unicode

class Verbosity(enum.IntEnum):
    """ Logger verbosity level """
    QUIET = 0
    ERROR = 1
    WARNING = 2
    INFO = 3
    DEBUG = 4
    VERBOSE = 5
    VERY_VERBOSE = 6

    def __str__(self) -> str:
        return super(Verbosity, self).__str__().split(".")[-1]


#pylint: disable=too-few-public-methods
class LogEvent(abc.ABC):
    """ Base class for Log Events """
    @property
    @abc.abstractmethod
    def _event_type(self) -> typing.List[str]:
        pass

    @property
    @abc.abstractmethod
    def _verbosity_level(self) -> Verbosity:
        pass

    @abc.abstractmethod
    def _init(self) -> None:
        pass

    def __init__(self) -> None:
        self._log: typing.Optional[Logger] = None
        self._dict: typing.Dict[str, typing.Any] = dict()

    def _init_dict(self) -> None:
        self._dict["type"] = self._event_type
        self._dict["time"] = time.ctime()

    def log_print(self,
                  msg: str,
                  *args: typing.Any,
                  **kwargs: typing.Any) -> None:
        """ Try printing something to stdout. Whether that actually happens
            depends on the verbosity setting """
        if isinstance(self._log, Logger):
            self._log.log_print(msg, self, *args, **kwargs)
        else:
            raise Exception("Printing before initialisation")


class ShellCommandLogEvent(LogEvent):
    """
    Log event for shell commands

    :param sh: Shell/Machine type
    :type sh: list(str)
    :param command: The command that was executed
    :type command: str
    :param prefix: An optional prefix to print before output lines
    :type prefix: str
    :param log_show: Whether documentation backends should include this command
    :type log_show: bool
    :param log_show_stdout: Whether documentation backends should include this
        commands output
    :type log_show_stdout: bool
    """
    #pylint: disable=too-many-arguments
    def __init__(self,
                 sh: typing.List[str],
                 command: str,
                 prefix: str = "   ## ",
                 log_show: bool = True,
                 log_show_stdout: bool = True) -> None:
        super().__init__()
        self.sh = sh
        self.output = ""
        self.prefix = prefix
        self._dict["command"] = command
        self._dict["show"] = log_show
        self._dict["show_stdout"] = log_show_stdout
        self.verbosity = Verbosity.VERBOSE

    def _init(self) -> None:
        shell_type_string = "("
        for i in range(0, len(self.sh) - 1):
            shell_type_string += self.sh[i] + ", "
        shell_type_string += self.sh[-1] + ")"
        cmd = repr(self._dict['command'])[1:-1]
        self.log_print(f"{shell_type_string} {cmd}")

    def add_line(self, line: str) -> None:
        """
        Add a line of stdout to this log event

        :param line: The line to be added
        :type line: str
        """
        if not line == "":
            self.output += line + ('' if line[-1] == '\n' else '\n')
        else:
            self.output += '\n'
        self.verbosity = Verbosity.VERY_VERBOSE
        for print_line in line.split('\n'):
            self.log_print("\x1B[0m" + self.prefix + print_line, prefix_dash=False)
        self.verbosity = Verbosity.VERBOSE
        self._dict["output"] = self.output

    def finished(self, exit_code: int) -> None:
        """
        Tell the log event that the command is done

        :param exit_code: The commands exit code
        :type exit_code: int
        """
        self._dict["output"] = self.output
        self._dict["exit_code"] = exit_code

    @property
    def _verbosity_level(self) -> Verbosity:
        return self.verbosity

    @property
    def _event_type(self) -> typing.List[str]:
        ev_type = ["shell"]
        ev_type.extend(self.sh)

        return ev_type


class TestcaseBeginLogEvent(LogEvent):
    """
    Log event for the start of a testcase

    :param tc_name: Name of the testcase
    :type tc_name: str
    :param layer: Call graph depth
    :type layer: int
    """
    def __init__(self, tc_name: str, layer: int) -> None:
        super().__init__()
        self._dict["name"] = tc_name
        self.tc = tc_name
        self.layer = layer

    def _init(self) -> None:
        msg = ""
        prfx = has_unicode("│   ", "|   ")
        for _ in range(0, self.layer):
            msg += prfx
        msg += has_unicode(
            f"├─Calling \x1B[1;34m{self.tc}\x1B[0m ... ",
            f"+-Calling \x1B[1;34m{self.tc}\x1B[0m ... ",
        )
        self.log_print(msg, False)

    @property
    def _verbosity_level(self) -> Verbosity:
        return Verbosity.INFO

    @property
    def _event_type(self) -> typing.List[str]:
        return ["testcase", "begin"]

class ExceptionLogEvent(LogEvent):
    """
    Log event for an exception

    :param exc_name: Name of the exception
    :type exc_name: str
    :param trace: Stack trace
    :type trace: str
    """

    def __init__(self, exc_name: str, trace: str) -> None:
        super().__init__()
        self._dict["name"] = exc_name
        self._dict["trace"] = trace
        self.name = exc_name

    def _init(self) -> None:
        self.log_print(f"Catched exception: {self.name}")

    @property
    def _verbosity_level(self) -> Verbosity:
        return Verbosity.DEBUG

    @property
    def _event_type(self) -> typing.List[str]:
        return ["exception"]


class TestcaseEndLogEvent(LogEvent):
    """
    Log event for the end of testcase

    :param tc_name: Name of the testcase
    :type tc_name: str
    :param layer: Call graph depth
    :type layer: int
    :param duration: Duration of the testcase in seconds
    :type duration: float
    :param success: Whether the testcase succeeded
    :type success: bool
    """
    #pylint: disable=too-many-arguments
    def __init__(self,
                 tc_name: str,
                 layer: int,
                 duration: float,
                 success: bool = True,
                 fail_ok: bool = False) -> None:
        super().__init__()
        self._dict["name"] = tc_name
        self._dict["duration"] = duration
        self._dict["success"] = success
        self._dict["fail_ok"] = fail_ok
        self.layer = layer
        self.success = success
        self.fail_ok = fail_ok

    def _init(self) -> None:
        msg = ""
        prfx = has_unicode("│   ", "|   ")
        for _ in range(0, self.layer):
            msg += prfx
        if self.success:
            msg += has_unicode(
                "│   └─\x1B[1;32mDone.\x1B[0m",
                "|   \\-\x1B[1;32mDone.\x1B[0m",
            )
        else:
            if self.fail_ok:
                msg += has_unicode(
                    "│   └─\x1B[1;33mFail expected.\x1B[0m",
                    "|   \\-\x1B[1;33mFail expected.\x1B[0m",
                )
            else:
                msg += has_unicode(
                    "│   └─\x1B[1;31mFail.\x1B[0m",
                    "|   \\-\x1B[1;31mFail.\x1B[0m",
                )
        self.log_print(msg, False)

    @property
    def _verbosity_level(self) -> Verbosity:
        return Verbosity.INFO

    @property
    def _event_type(self) -> typing.List[str]:
        return ["testcase", "end"]


class TBotFinishedLogEvent(LogEvent):
    """
    Log event for the end of a TBot run

    :param success: Whether this run was successful
    :type success: bool
    """
    def __init__(self, success: bool) -> None:
        super().__init__()
        self._dict["success"] = success
        self.success = success

    def _init(self) -> None:
        if self.success:
            self.log_print(
                has_unicode(
                    "└─Done, \x1B[1;32mSUCCESS\x1B[0m\n",
                    "\\-Done, \x1B[1;32mSUCCESS\x1B[0m\n",
                ), False)
        else:
            self.log_print(
                has_unicode(
                    "└─Done, \x1B[1;31mFAILURE\x1B[0m\n",
                    "\\-Done, \x1B[1;31mFAILURE\x1B[0m\n",
                ), False)

    @property
    def _verbosity_level(self) -> Verbosity:
        return Verbosity.INFO

    @property
    def _event_type(self) -> typing.List[str]:
        return ["tbot", "end"]


class CustomLogEvent(LogEvent):
    """
    Custom Log Event

    :param ty: Type of the log event
    :type ty: list(str)
    :param stdout: Optional text to be printed to TBot's stdout
    :type stdout: str
    :param verbosity: Verbosity of this log event
    :type verbosity: tbot.logger.Verbosity
    :param dict_values: Additional dict values to be added to the log
    :type dict_values: dict
    """
    def __init__(self,
                 ty: typing.List[str],
                 stdout: typing.Optional[str] = None,
                 verbosity: Verbosity = Verbosity.INFO,
                 dict_values: typing.Optional[typing.Dict[str, typing.Any]] = None) -> None:
        super().__init__()
        if dict_values is not None:
            self._dict = dict_values
        self.stdout = stdout
        self.ty = ty
        self.verbosity = verbosity

    def _init(self) -> None:
        if self.stdout is not None:
            self.log_print(self.stdout)

    @property
    def _verbosity_level(self) -> Verbosity:
        return self.verbosity

    @property
    def _event_type(self) -> typing.List[str]:
        return self.ty


class Logger:
    """
    TBot Logger

    :param verbosity: Minimum verbosity level for printing to stdout
    :type verbosity: tbot.logger.Verbosity
    :param logfile: Where to store the ``json.log``
    :type logfile: str
    """
    def __init__(self, verbosity: Verbosity, logfile: pathlib.Path) -> None:
        self.logevents: typing.List[LogEvent] = list()
        self.verbosity = verbosity
        self.logfile = logfile
        self.layer = 0
        print("\x1B[33;1mTBot\x1B[0m starting ...")

    def log(self, ev: LogEvent) -> None:
        """ Log a log event """
        #pylint: disable=protected-access
        ev._log = self
        self.logevents.append(ev)
        ev._init_dict()
        ev._init()

    def doc_log(self, text: str) -> None:
        """
        Create a log event for documentation generating backends with some
        text to be added

        :param text: The text
        :type text: str
        """
        ev = CustomLogEvent(["doc", "text"], dict_values={"text": text})
        self.log(ev)

    def doc_appendix(self, title: str, text: str) -> None:
        """
        Create a log event for documentation generating backends which hints
        for an appendix to be created

        :param title: Title of the appendix
        :type title: str
        :param text: Text of the appendix
        :type text: str
        """
        ev = CustomLogEvent(
            ["doc", "appendix"],
            dict_values={"text": text, "title": title})
        self.log(ev)

    def log_msg(self, message: str, verbosity: Verbosity = Verbosity.INFO) -> None:
        """
        A shortcut for writing a message to stdout

        :param message: Text to be written to stdout
        :type message: str
        :param verbosity: Minimum verbosity level for this message to be written
        :type verbosity: tbot.logger.Verbosity
        :returns: Nothing
        """
        ev = CustomLogEvent(
            ["msg", str(verbosity)],
            verbosity=verbosity,
            stdout=message,
            dict_values={"text": message})
        self.log(ev)

    def log_debug(self, message: str) -> None:
        """
        Shortcut for debug messages

        :param message: Debug message
        :type message: str
        :returns: Nothing
        """
        self.log_msg(message, Verbosity.DEBUG)

    def write_logfile(self, filename: typing.Optional[pathlib.PurePosixPath] = None) -> None:
        """
        Write log to a file

        :param filename: Optional alternative log file. If this is None,
            the logfile supplied on init will be used.
        :type filename: str
        """
        #pylint: disable=protected-access
        json.dump([ev._dict for ev in self.logevents],
                  open(self.logfile if filename is None else filename, "w"),
                  indent=4)

    def log_print(self,
                  msg: str,
                  ev: LogEvent,
                  prefix: bool = True,
                  prefix_dash: bool = True) -> None:
        """
        Try printing to stdout. This is influenced by the
        verbosity level of the LogEvent.

        :param msg: The text to be printed.
        :type msg: str
        :param ev: The :class:`~tbot.logger.LogEvent` this print call originated
            from
        :type ev: tbot.logger.LogEvent
        :param prefix: Whether to add a prefix to match other outputs indent
        :type prefix: bool
        :param prefix_dash: Whether this prefix is supposed to contain a dash
        :type prefix_dash: bool
        """

        #pylint: disable=protected-access
        if ev._verbosity_level <= self.verbosity:
            for i, line in enumerate(msg.split('\n')):
                msg_prefix = "\x1B[0m"
                if prefix is True:
                    prfx = has_unicode("│   ", "|   ")
                    for _ in range(0, self.layer):
                        msg_prefix += prfx
                    if prefix_dash and i == 0:
                        msg_prefix += has_unicode("├─", "+-")
                    else:
                        msg_prefix += has_unicode("│ ", "| ")
                print(msg_prefix + line)
