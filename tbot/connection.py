""" SSH Connection to lab pc """
import paramiko


class Connection:
    """ SSH Connection to lab pc """
    def __init__(self, hostname, **kwargs):
        """ Connect to VLab PC """
        conn = paramiko.SSHClient()
        conn.load_system_host_keys()
        conn.connect(hostname, **kwargs)

        self.raw_conn = conn

    def _simple_command(self, tb, command, environment=None):
        # TODO: Remove
        """ Execute a command and return the exit status """
        command_lines = command.split("\n")
        tb.log.log_stdout(f"<$HELL> {command_lines[0]}")
        if len(command_lines) > 1:
            for line in command_lines[1:]:
                tb.log.log_stdout(f"CONT>>> {line}")
        _, sout, _ = self.raw_conn.exec_command(command,
                                                environment=environment)
        tb.log.log_stdout(sout.read().decode("utf-8")[:-1])
        return sout.channel.recv_exit_status()
