"""
Machines
--------
"""
import abc
import typing
import paramiko
import tbot

KWARGS_LIST = [
    ("lab.port", "port"),
    ("lab.user", "username"),
    ("lab.password", "password"),
    ("lab.keyfile", "key_filename"),
    ]

class Machine(abc.ABC):
    """ Abstract base class for machines """
    def __init__(self) -> None:
        self._log: typing.Optional[tbot.logger.Logger] = None

    def _setup(self, tb: 'tbot.TBot') -> None:
        self._log = tb.log

    def _destruct(self, tb: 'tbot.TBot') -> None:
        pass

    @abc.abstractmethod
    def _exec(self,
              command: str,
              log_event: tbot.logger.LogEvent) -> typing.Tuple[int, str]:
        pass

    @abc.abstractproperty
    def common_machine_name(self) -> str:
        """ Common name of this machine, eg ``"board"`` or ``"labhost"`` """
        pass

    @abc.abstractproperty
    def unique_machine_name(self) -> str:
        """ Unique name of this machine, eg ``"labhost-noenv"`` """
        pass

    def exec(self,
             command: str,
             log_show: bool = True,
             log_show_stdout: bool = True) -> typing.Tuple[int, str]:
        """
        Execute a command on this machine

        :param command: The command to be executed, no newline at the end
        :param log_show: Whether documentation backends should include this command
        :param log_show_stdout: Whether documentation backends should include the stdout
            of this command
        :returns: A tuple of the return code and the output (stdout and stderr are merged)
        """
        log_event = tbot.logger.ShellCommandLogEvent(self.unique_machine_name.split('-'),
                                                     command,
                                                     log_show=log_show,
                                                     log_show_stdout=log_show_stdout)
        if isinstance(self._log, tbot.logger.Logger):
            self._log.log(log_event)
        ret = self._exec(command, log_event)
        log_event.finished(ret[0])
        return ret

    def exec0(self, command: str, **kwargs: bool) -> str:
        """
        Execute a command and expect it to return with 0

        :param command: The command to be executed, no newline at the end
        :param kwargs: Passed through to Machine.exec
        :returns: The output (stdout and stderr are merged)
        """
        ret = self.exec(command, **kwargs)
        assert ret[0] == 0, f"Command \"{command}\" failed:\n{ret[1]}"
        return ret[1]

class MachineManager(dict):
    """ A container to manage the list of available machines """
    def __init__(self, tb: 'tbot.TBot', conn: typing.Optional[paramiko.SSHClient] = None) -> None:
        if isinstance(conn, paramiko.SSHClient):
            self.connection = conn
        else:
            self.connection = paramiko.SSHClient()
            self.connection.load_system_host_keys()

            kwargs = dict(filter(lambda arg: arg[1] is not None,
                                 map(lambda arg:
                                     (arg[1], tb.config[arg[0], None]),
                                     KWARGS_LIST)))
            self.connection.connect(tb.config["lab.hostname"], **kwargs)

        super().__init__()
