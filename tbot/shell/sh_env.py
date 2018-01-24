""" A shell with environment """
import socket
import random
import tbot.shell


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
        # Resize the pty to ensure we do not get escape sequences from the terminal
        # trying to wrap to the next line
        self.channel.resize_pty(200, 200, 1000, 1000)
        self.channel.invoke_shell()

        self.log_event = None

        # Set custom prompt to know when output ends
        self.prompt = f"TBOT-{random.randint(100000, 999999)}>"
        self.channel.send(f"""\
PROMPT_COMMAND=''
PS1='{self.prompt}'
""")
        self._read_to_prompt()

    def _read_to_prompt(self):
        buf = ""

        last_newline = 0

        try:
            while True:
                # Read a lot and hope that this is all there is, so
                # we don't cut off inside a unicode sequence and fail
                buf_data = self.channel.recv(10000000)
                buf_data = buf_data.decode("utf-8")

                # Fix '\r's, replace '\r\n' twice to avoid some glitches
                buf_data = buf_data.replace('\r\n', '\n') \
                    .replace('\r\n', '\n') \
                    .replace('\r', '\n')

                buf += buf_data

                if self.log_event is not None:
                    while "\n" in buf[last_newline:]:
                        line = buf[last_newline:].split('\n')[0]
                        if last_newline != 0:
                            self.log_event.add_line(line)
                        last_newline += len(line) + 1

                if buf[-len(self.prompt):] == self.prompt:
                    # Print rest of last line to make sure nothing gets lost
                    if self.log_event is not None and "\n" not in buf[last_newline:]:
                        line = buf[last_newline:-len(self.prompt)]
                        if line != "":
                            self.log_event.add_line(line)
                    break
        except UnicodeDecodeError:
            return ""

        return buf

    def _exec(self, command, log_event):
        self.channel.send(f"{command}\n")
        try:
            self.log_event = log_event
            stdout = self._read_to_prompt()[len(command)+1:-len(self.prompt)]
        except socket.timeout:
            stdout = ""

        self.log_event = None

        # return code parsing
        self.channel.send("echo $?\n")
        retcode_stdout = self._read_to_prompt()
        retcode_stdout = retcode_stdout[len("echo $?")+1:-len(self.prompt)]
        retcode_stdout = retcode_stdout.strip()
        return int(retcode_stdout), stdout

    def _shell_type(self):
        return ("sh", "env")
