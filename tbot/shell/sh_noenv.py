""" A Shell without environment """
import paramiko
import tbot.shell

KWARGS_LIST = [
    ("lab.port", "port"),
    ("lab.user", "username"),
    ("lab.password", "password"),
    ("lab.keyfile", "key_filename"),
    ]


class ShellShNoEnv(tbot.shell.Shell):
    """ A Shell without environment. This reduces side effects """
    def _init_session(self, tb):
        if tb.shell is None:
            self.conn = paramiko.SSHClient()
            self.conn.load_system_host_keys()
            kwargs = dict(filter(lambda arg: arg[1] is not None,
                                 map(lambda arg:
                                     (arg[1], tb.config.try_get(arg[0])),
                                     KWARGS_LIST)))
            self.conn.connect(tb.config.get("lab.hostname"), **kwargs)
        else:
            self.conn = tb.shell.conn

    def _exec(self, command, log_event):
        channel = self.conn.get_transport().open_session()
        channel.set_combine_stderr(True)
        channel.exec_command(command)
        stdout = channel.makefile().read()
        ret_code = channel.recv_exit_status()

        output = ""
        if stdout[-1] == 10:
            output = stdout[:-1].decode("utf-8")
        else:
            output = stdout.decode("utf-8")

        for line in output.split("\n"):
            log_event.add_line(line)
        return ret_code, output

    def _shell_type(self):
        return ("sh", "noenv")
