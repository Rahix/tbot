import abc
import paramiko
import tbot.logger

KWARGS_LIST = [
    ("lab.port", "port"),
    ("lab.user", "username"),
    ("lab.password", "password"),
    ("lab.keyfile", "key_filename"),
    ]

class Machine(abc.ABC):
    def __init__(self):
        self._log = "foo"

    def _setup(self, tb):
        self._log = tb.log

    def _destruct(self):
        pass

    @abc.abstractmethod
    def _exec(self, command, log_event):
        pass

    @abc.abstractproperty
    def default_machine_name(self):
        pass

    @abc.abstractproperty
    def unique_machine_name(self):
        pass

    def exec(self, command, log_show=True, log_show_stdout=True):
        log_event = tbot.logger.ShellCommandLogEvent(self.unique_machine_name.split('-'),
                                                     command,
                                                     log_show=log_show,
                                                     log_show_stdout=log_show_stdout)
        self._log.log(log_event)
        ret = self._exec(command, log_event)
        log_event.finished(ret[0])
        return ret

    def exec0(self, command, **kwargs):
        ret = self.exec(command, **kwargs)
        assert ret[0] == 0, f"Command \"{command}\" failed:\n{ret[1]}"
        return ret[1]

class MachineManager(dict):
    def __init__(self, tb):
        self.connection = paramiko.SSHClient()
        self.connection.load_system_host_keys()

        kwargs = dict(filter(lambda arg: arg[1] is not None,
                             map(lambda arg:
                                 (arg[1], tb.config.try_get(arg[0])),
                                 KWARGS_LIST)))
        self.connection.connect(tb.config.get("lab.hostname"), **kwargs)

        super().__init__()
