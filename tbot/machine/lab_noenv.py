"""
Labhost machine without environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
"""
import typing
import pathlib
import paramiko
import tbot
import tbot.config
from . import machine


class MachineLabNoEnv(machine.Machine):
    """ Labhost machine without environment """

    def __init__(self) -> None:
        super().__init__()
        self._workdir = None
        self.conn: typing.Optional[paramiko.SSHClient] = None

    def _setup(
        self, tb: "tbot.TBot", previous: typing.Optional[machine.Machine] = None
    ) -> "MachineLabNoEnv":
        self.conn = tb.machines.connection
        super()._setup(tb, previous)
        self._workdir = tb.config["tbot.workdir", None]
        return self

    def _exec(
        self, command: str, stdout_handler: typing.Optional[tbot.log.LogStdoutHandler]
    ) -> typing.Tuple[int, str]:
        assert isinstance(
            self.conn, paramiko.SSHClient
        ), "Machine was not initialized correctly!"
        channel = self.conn.get_transport().open_session()
        channel.set_combine_stderr(True)
        channel.exec_command(command)
        stdout = channel.makefile().read()
        ret_code = channel.recv_exit_status()

        output = stdout.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")

        # TODO: Make output appear instantly and not after the run is done
        lines = output.strip("\n").split("\n")
        if isinstance(stdout_handler, tbot.log.LogStdoutHandler) and not (
            len(lines) == 1 and lines[0] == ""
        ):
            for line in lines:
                stdout_handler.print(line)
        return ret_code, output

    @property
    def workdir(self) -> pathlib.PurePosixPath:
        if self._workdir is None:
            raise tbot.config.InvalidConfigException("No workdir specified")
        return self._workdir

    @property
    def common_machine_name(self) -> str:
        """ Common name of this machine, always ``"host"`` """
        return "host"

    @property
    def unique_machine_name(self) -> str:
        """ Unique name of this machine, always ``"labhost-noenv"`` """
        return "labhost-noenv"
