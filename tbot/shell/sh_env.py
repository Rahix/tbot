""" A shell with environment """
import socket
import random
import tbot.shell


# TODO: Make this interface way more stable
class ShellShEnv(tbot.shell.Shell):
    """ Shell with environment (Only use this if you have to. Prefer using
        a noenv shell for reduced side effects """
    def _init_session(self, tb):
        if tb.shell is None:
            # Create a noenv shell as a base
            tb.shell = tbot.shell.sh_noenv.ShellShNoEnv(tb)

        self.conn = tb.shell.conn
        self.channel = self.conn.get_transport().open_session()
        self.channel.get_pty()
        self.channel.invoke_shell()
        self.channel_file = self.channel.makefile("rw")

        self.log_event = None

        # Set custom prompt to know when output ends
        self.prompt = f"TBOT-{random.randint(100000, 999999)}>"
        self.channel_file.write(f"""\
PROMPT_COMMAND=''
PS1='{self.prompt}'

""")
        self._read_to_prompt()

    def _read_to_prompt(self):
        buf = ""
        line = ""
        while len(line) < len(self.prompt) or \
                (not line[:len(self.prompt)] == self.prompt):
            buf += line
            line = self.channel_file.readline()
            line = line[:-2] + "\n" if line[-2] == "\r" else line
            if self.log_event is not None:
                self.log_event.add_line(line[:-1])

        return buf

    def _exec(self, command, log_event):
        self.channel_file.write(f"{command}\n\n")
        self.log_event = log_event
        try:
            self._read_to_prompt()
            stdout = self._read_to_prompt()
        except socket.timeout:
            stdout = ""

        self.channel_file.write("echo $?\n\n")
        self._read_to_prompt()
        stdout_ret_code = self._read_to_prompt()
        ret_code = int(stdout_ret_code)
        self.log_event = None

        return ret_code, stdout[:-1]

    def _shell_type(self):
        return ("sh", "env")
