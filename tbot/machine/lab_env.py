import random
import typing
import socket
import paramiko
import tbot
from . import machine

class MachineLabEnv(machine.Machine):
    def __init__(self, prompt: typing.Optional[str] = None) -> None:
        self.channel: typing.Optional[paramiko.Channel] = None

        # Set custom prompt to know when output ends
        self.prompt = f"TBOT-{random.randint(100000, 999999)}>"
        if isinstance(prompt, str):
            self.prompt = prompt

        super().__init__()

    def _setup(self, tb: 'tbot.TBot') -> None:
        conn = tb.machines.connection
        self.channel = conn.get_transport().open_session()
        self.channel.get_pty()
        # Resize the pty to ensure we do not get escape sequences from the terminal
        # trying to wrap to the next line
        self.channel.resize_pty(200, 200, 1000, 1000)
        self.channel.invoke_shell()

        # Initialize remote shell
        self.channel.send(f"""\
PROMPT_COMMAND=''
PS1='{self.prompt}'
""")
        self._read_to_prompt(None)

        super()._setup(tb)

    def _read_to_prompt(self, log_event: tbot.logger.LogEvent) -> str:
        buf = ""

        last_newline = 0

        if not isinstance(self.channel, paramiko.Channel):
            raise Exception("Channel not initialized")

        try:
            while True:
                # Read a lot and hope that this is all there is, so
                # we don't cut off inside a unicode sequence and fail
                # TODO: Make this more robust
                buf_data = self.channel.recv(10000000)
                buf_data = buf_data.decode("utf-8")

                # Fix '\r's, replace '\r\n' twice to avoid some glitches
                buf_data = buf_data.replace('\r\n', '\n') \
                    .replace('\r\n', '\n') \
                    .replace('\r', '\n')

                buf += buf_data

                if log_event is not None:
                    while "\n" in buf[last_newline:]:
                        line = buf[last_newline:].split('\n')[0]
                        if last_newline != 0:
                            log_event.add_line(line)
                        last_newline += len(line) + 1

                if buf[-len(self.prompt):] == self.prompt:
                    # Print rest of last line to make sure nothing gets lost
                    if log_event is not None and "\n" not in buf[last_newline:]:
                        line = buf[last_newline:-len(self.prompt)]
                        if line != "":
                            log_event.add_line(line)
                    break
        except UnicodeDecodeError:
            return ""

        return buf

    def _command(self,
                 command: str,
                 log_event: tbot.logger.LogEvent) -> str:
        if not isinstance(self.channel, paramiko.Channel):
            raise Exception("Channel not initialized")

        self.channel.send(f"{command}\n")
        try:
            # Read until next occurence of the prompt. Then cut of the first part,
            # which is the command with a newline, and the last part, which is the
            # prompt for the next command
            stdout = self._read_to_prompt(log_event)[len(command)+1:-len(self.prompt)]
        except socket.timeout:
            # TODO: Better exception handling
            stdout = ""

        return stdout

    def _exec(self,
              command: str,
              log_event: tbot.logger.LogEvent) -> typing.Tuple[int, str]:
        stdout = self._command(command, log_event)

        # Get the return code
        retcode = int(self._command("echo $?", None).strip())

        return retcode, stdout

    @property
    def common_machine_name(self) -> str:
        return "labhost"

    @property
    def unique_machine_name(self) -> str:
        return "labhost-env"
