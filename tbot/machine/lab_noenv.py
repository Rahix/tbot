import tbot.machine

class MachineLabNoEnv(tbot.machine.Machine):
    def _setup(self, tb):
        self.conn = tb.machines.connection
        super()._setup(tb)

    def _exec(self, command, log_event):
        channel = self.conn.get_transport().open_session()
        channel.set_combine_stderr(True)
        channel.exec_command(command)
        stdout = channel.makefile().read()
        ret_code = channel.recv_exit_status()

        output = stdout.decode("utf-8") \
            .replace('\r\n', '\n') \
            .replace('\r', '\n')

        for line in output.strip('\n').split('\n'):
            log_event.add_line(line)
        return ret_code, output

    def default_machine_name(self):
        return "labhost"
