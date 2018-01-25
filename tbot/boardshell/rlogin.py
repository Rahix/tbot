""" A board shell implementation """
import random
import time
import tbot.boardshell
import tbot.shell.sh_env
import tbot.shell.sh_noenv


#pylint: disable=too-many-instance-attributes
class BoardShellRLogin(tbot.boardshell.BoardShell):
    """ RLogin board shell, can be used with other similar tools as well """
    def _init_session(self, tb):
        self.shellname = tb.config.get("board.shell.name")

        # Use a noenv shell for power control
        self.noenv_shell = tbot.shell.sh_noenv.ShellShNoEnv(tb)

        # Power
        self.power_cmd_on = tb.config.get("board.power.on_command")
        self.power_cmd_off = tb.config.get("board.power.off_command")

        # Use an env shell as a base
        self.conn = tb.shell.conn \
            if tb.shell is not None \
            else self.noenv_shell.conn

        self.channel = self.conn.get_transport().open_session()
        self.channel.get_pty()
        # Resize the pty to ensure we do not get escape sequences from the terminal
        # trying to wrap to the next line
        self.channel.resize_pty(200, 200, 1000, 1000)
        self.channel.invoke_shell()

        self.prompt = f"TBOT-BS-START-{random.randint(11111,99999)}>"

        self.connect_command = tb.config.get("board.shell.command")
        self.uboot_prompt = tb.config.get("board.shell.prompt")
        self.uboot_timeout = tb.config.get("board.shell.timeout", 2)

        self.log_event = None
        self.is_on = False

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

    def poweron(self):
        if not self.is_on:
            self.channel.send(f"PROMPT_COMMAND=\nPS1='{self.prompt}'\n")

            self._read_to_prompt()
            self.channel.send(f"{self.connect_command}\n")
            self.noenv_shell.exec0(self.power_cmd_on, log_show_stdout=False)

            # Stop autoboot
            time.sleep(self.uboot_timeout)
            self.channel.send("\n")
            self.prompt = self.uboot_prompt
            boot_stdout = self._read_to_prompt()
            self.is_on = True
            return boot_stdout

        return ""

    def _cleanup_boardstate(self):
        self.channel.close()
        self.noenv_shell.exec0(self.power_cmd_off, log_show_stdout=False)

    def _exec(self, command, log_event):
        assert self.is_on, "Trying to execute commands on a turned off board"
        log_event.prefix = "   >> "
        self.log_event = log_event
        self.channel.send(command + "\n")
        stdout = self._read_to_prompt()[len(command)+1:-len(self.prompt)]

        self.log_event = None

        # return code parsing
        self.channel.send("echo $?\n")
        retcode_stdout = self._read_to_prompt()
        retcode_stdout = retcode_stdout[len("echo $?")+1:-len(self.prompt)]
        retcode_stdout = retcode_stdout.strip()
        return int(retcode_stdout), stdout

    def _board_shell_type(self):
        return ("rlogin", self.shellname)
