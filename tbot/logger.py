""" TBOT Logger """
import abc
import time
import json
import enum


class Verbosity(enum.IntEnum):
    """ Logger verbosity level """
    QUIET = 0
    ERROR = 1
    WARNING = 2
    INFO = 3
    VERBOSE = 4
    VERY_VERBOSE = 5
    DEBUG = 6


#pylint: disable=too-few-public-methods
class LogEvent(abc.ABC):
    """ Base class for Log Events """
    @property
    @abc.abstractmethod
    def _event_type(self):
        pass

    @property
    @abc.abstractmethod
    def _verbosity_level(self):
        pass

    @abc.abstractmethod
    def _init(self):
        pass

    def __init__(self):
        self._log = None
        self._dict = dict()

    def _init_dict(self):
        self._dict["type"] = self._event_type
        self._dict["time"] = time.ctime()

    def log_print(self, msg):
        """ Try printing something to stdout. Whether that actually happens
            depends on the verbosity setting """
        self._log.log_print(msg, self)


class ShellCommandLogEvent(LogEvent):
    """ Log event for shell commands """
    #pylint: disable=too-many-arguments
    def __init__(self, sh, command, prefix="   ## ", log_show=True, log_show_stdout=True):
        super().__init__()
        self.sh = sh
        self.output = ""
        self.prefix = prefix
        self._dict["command"] = command
        self._dict["show"] = log_show
        self._dict["show_stdout"] = log_show_stdout
        self.verbosity = Verbosity.VERBOSE

    def _init(self):
        shell_type_string = "("
        for i in range(0, len(self.sh) - 1):
            shell_type_string += self.sh[i] + ", "
        shell_type_string += self.sh[-1] + ")"
        self.log_print(f"{shell_type_string} {self._dict['command']}")

    def add_line(self, line):
        """ Add a line of stdout to this log event """
        if not line == "":
            self.output += line + ('' if line[-1] == '\n' else '\n')
        else:
            self.output += '\n'
        self.verbosity = Verbosity.VERY_VERBOSE
        for print_line in line.split('\n'):
            self.log_print("\x1B[0m" + self.prefix + print_line)
        self.verbosity = Verbosity.VERBOSE

    def finished(self):
        """ Tell the log event that the command is done """
        self._dict["output"] = self.output

    @property
    def _verbosity_level(self):
        return self.verbosity

    @property
    def _event_type(self):
        ev_type = ["shell"]
        ev_type.extend(self.sh)

        return ev_type


class TestcaseBeginLogEvent(LogEvent):
    """ Log event for the start of a testcase """
    def __init__(self, tc_name, layer):
        super().__init__()
        self._dict["name"] = tc_name
        self.tc = tc_name
        self.layer = layer

    def _init(self):
        msg = ""
        for _ in range(0, self.layer):
            msg += "│   "
        msg += f"├─Calling \x1B[1;34m{self.tc}\x1B[0m ... "
        self.log_print(msg)

    @property
    def _verbosity_level(self):
        return Verbosity.INFO

    @property
    def _event_type(self):
        return ("testcase", "begin")


class TestcaseEndLogEvent(LogEvent):
    """ Log event for end of testcase """
    def __init__(self, tc_name, layer, duration):
        super().__init__()
        self._dict["name"] = tc_name
        self._dict["duration"] = duration
        self.layer = layer

    def _init(self):
        msg = ""
        for _ in range(0, self.layer):
            msg += "│   "
        msg += "│   └─\x1B[1;32mDone.\x1B[0m"
        self.log_print(msg)

    @property
    def _verbosity_level(self):
        return Verbosity.INFO

    @property
    def _event_type(self):
        return ("testcase", "end")


class TBotFinishedLogEvent(LogEvent):
    """ Log event for end of tbot """
    def __init__(self, success):
        super().__init__()
        self._dict["success"] = success
        self.success = success

    def _init(self):
        if self.success:
            self.log_print("└─Done, \x1B[1;32mSUCCESS\x1B[0m\n")
        else:
            self.log_print("└─Done, \x1B[1;31mFAILURE\x1B[0m\n")

    @property
    def _verbosity_level(self):
        return Verbosity.INFO

    @property
    def _event_type(self):
        return "tbotend"


class CustomLogEvent(LogEvent):
    """ Custom Log Event """
    def __init__(self, ty, stdout=None,
                 verbosity=Verbosity.INFO,
                 dict_values=None):
        super().__init__()
        if dict_values is not None:
            self._dict = dict_values
        self.stdout = stdout
        self.ty = ty
        self.verbosity = verbosity

    def _init(self):
        if self.stdout is not None:
            self.log_print(self.stdout)

    @property
    def _verbosity_level(self):
        return self.verbosity

    @property
    def _event_type(self):
        return self.ty


class Logger:
    """ TBOT Logger """
    def __init__(self, verbosity, logfile):
        self.logevents = list()
        self.verbosity = verbosity
        self.logfile = logfile

    def log(self, ev):
        """ Log a log event """
        #pylint: disable=protected-access
        ev._log = self
        self.logevents.append(ev)
        ev._init_dict()
        ev._init()

    def doc_log(self, text):
        """ Create a log event for documentation generating backends with some
            text to be added """
        ev = CustomLogEvent(["doc", "text"], dict_values={"text": text})
        self.log(ev)

    def doc_appendix(self, title, text):
        """ Create a log event for documentation generating backends with some
            text to be added """
        ev = CustomLogEvent(
            ["doc", "appendix"],
            dict_values={"text": text, "title": title})
        self.log(ev)

    def write_logfile(self, filename=None):
        """ Write log to a file """
        #pylint: disable=protected-access
        json.dump([ev._dict for ev in self.logevents],
                  open(self.logfile if filename is None else filename, "w"))

    def log_print(self, msg, ev):
        """ Try printing to stdout. This is influenced by the
            verbosity level """
        #pylint: disable=protected-access
        if ev._verbosity_level <= self.verbosity:
            print(msg)

    def __del__(self):
        self.write_logfile()
