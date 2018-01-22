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
        self.channel.invoke_shell()

        self.prompt = f"TBOT-BS-START-{random.randint(11111,99999)}>"

        self.connect_command = tb.config.get("board.shell.command")
        self.uboot_prompt = tb.config.get("board.shell.prompt")

        self.log_event = None
        self.is_on = False

    def _read_to_prompt(self):
        prompt_bytes = bytes(self.prompt, "utf-8")
        buf = b""

        last_newline = 0

        while True:
            buf_data = self.channel.recv(1024)
            buf += buf_data

            while b"\n" in buf[last_newline:]:
                line_nl = buf[last_newline:].split(b'\n')[0]
                line_nl_notrail = line_nl[:-1] if line_nl != b'' and line_nl[-1] == 13 else line_nl
                if self.log_event is not None:
                    if last_newline != 0:
                        for line in line_nl_notrail.split(b'\r'):
                            self.log_event.add_line(line.decode('utf-8'))
                last_newline += len(line_nl) + 1

            if buf[-len(prompt_bytes):] == prompt_bytes:
                break

        # Sometimes the boards sent something before booting.
        # This makes sure, we don't panic if that is not decodable.
        try:
            return buf.decode("utf-8")
        except UnicodeDecodeError:
            return ""

    def poweron(self):
        self.channel.send(f"PROMPT_COMMAND=\nPS1='{self.prompt}'\n")

        self._read_to_prompt()
        self.channel.send(f"{self.connect_command}\n")
        self.noenv_shell.exec0(self.power_cmd_on, log_show_stdout=False)

        # Stop autoboot
        # TODO: Make timeout configurable
        time.sleep(2)
        self.channel.send("\n")
        self.prompt = self.uboot_prompt
        boot_stdout = self._read_to_prompt()
        self.is_on = True
        return boot_stdout

    def _cleanup_boardstate(self):
        self.channel.close()
        self.noenv_shell.exec0(self.power_cmd_off, log_show_stdout=False)

    def _exec(self, command, log_event):
        if not self.is_on:
            raise "Trying to execute commands on a turned off board"
        log_event.prefix = "   >> "
        self.log_event = log_event
        self.channel.send(command + "\n")
        stdout = self._read_to_prompt()[len(command)+2:-len(self.prompt)]
        stdout = stdout.replace("\r\n", "\n")
        self.log_event = None
        # return code parsing
        self.channel.send("echo $?\n")
        retcode_stdout = self._read_to_prompt()
        retcode_stdout = retcode_stdout[len("echo $?")+2:-len(self.prompt)]
        retcode_stdout = retcode_stdout.strip()
        return (int(retcode_stdout), stdout)

    def _board_shell_type(self):
        return ("rlogin", self.shellname)
