""" Abstract base class for shells """
import abc
import tbot.logger


class Shell(abc.ABC):
    """ Base class for shells """
    @abc.abstractmethod
    def _init_session(self, tb):
        """ Start a shell session """
        pass

    @abc.abstractmethod
    def _exec(self, command, log_event):
        """ Actually execute a command """
        pass

    @abc.abstractmethod
    def _shell_type(self):
        """ Return identifier for this shell type """
        pass

    def __init__(self, tb):
        self.tb = tb
        self._log = tb.log
        self._init_session(tb)
        self.shell_type_string = "("
        self.shell_type = self._shell_type()
        for i in range(0, len(self.shell_type) - 1):
            self.shell_type_string += self.shell_type[i] + ", "
        self.shell_type_string += self.shell_type[-1] + ")"

    def exec(self, command, log_show=True):
        """ Execute a command in this shell """
        log_event = tbot.logger.ShellCommandLogEvent(self.shell_type,
                                                     command,
                                                     log_show=log_show)
        self._log.log(log_event)
        ret = self._exec(command, log_event)
        log_event.finished()
        return ret

    def exec0(self, command, **kwargs):
        """ Execute a command in this shell and make sure it succeeds
            (Returncode is checked to be 0) """
        ret = self.exec(command, **kwargs)
        assert ret[0] == 0, f"Command \"{command}\" failed:\n{ret[1]}"
        return ret[1]
