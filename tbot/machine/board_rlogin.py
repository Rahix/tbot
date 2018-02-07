"""
Board machine for rlogin like interfaces
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
"""
import random
import time
import typing
import paramiko
import tbot
from . import board

#pylint: disable=too-many-instance-attributes
class MachineBoardRlogin(board.MachineBoard):
    """ Board machine for rlogin like interfaces """
    def __init__(self) -> None:
        self.name = "unknown"

        self.power_cmd_on = ""
        self.power_cmd_off = ""
        self.connect_command = ""

        self.prompt = f"TBOT-BS-START-{random.randint(11111,99999)}>"
        self.uboot_prompt = "U-Boot> "
        self.uboot_timeout = 2

        self.channel: typing.Optional[paramiko.Channel] = None
        self.noenv: typing.Optional[tbot.machine.Machine] = None

        super().__init__()

    def _setup(self, tb: 'tbot.TBot') -> None:
        super()._setup(tb)
        self.name = tb.config.get("board.shell.name", self.name)

        self.power_cmd_on = tb.config.get("board.power.on_command")
        self.power_cmd_off = tb.config.get("board.power.off_command")

        conn = tb.machines.connection
        self.channel = conn.get_transport().open_session()
        self.channel.get_pty()

        # Resize the pty to ensure we do not get escape sequences from the terminal
        # trying to wrap to the next line
        self.channel.resize_pty(200, 200, 1000, 1000)
        self.channel.invoke_shell()

        self.connect_command = tb.config.get("board.shell.command")
        self.uboot_prompt = tb.config.get("board.shell.prompt", self.uboot_prompt)
        self.uboot_timeout = tb.config.get("board.shell.timeout", self.uboot_timeout)

        # Save the noenv shell to have it accessible later
        self.noenv = tb.machines["labhost-noenv"]

        # Poweron the board
        self.channel.send(f"PROMPT_COMMAND=\nPS1='{self.prompt}'\n")
        self._read_to_prompt(None)
        self.channel.send(f"{self.connect_command}\n")

        self.noenv.exec0(self.power_cmd_on, log_show_stdout=False)

        # Stop autoboot
        time.sleep(self.uboot_timeout)
        self.channel.send("\n")
        self.prompt = self.uboot_prompt
        boot_stdout = self._read_to_prompt(None)

        ev = tbot.logger.CustomLogEvent(
            ["board", "boot"],
            stdout="\x1B[1mBOARD POWERUP\x1B[0m",
            verbosity=tbot.logger.Verbosity.INFO,
            dict_values={"log": boot_stdout})

        tb.log.log(ev)

    def _destruct(self, tb: 'tbot.TBot') -> None:
        if isinstance(self.noenv, tbot.machine.Machine):
            self.noenv.exec0(self.power_cmd_off, log_show_stdout=False)
        else:
            raise Exception("noenv shell not initialized correctly, board might still be on!")
        if isinstance(self.channel, paramiko.Channel):
            self.channel.close()
        else:
            raise Exception("Channel not initilized")

    def _read_to_prompt(self, log_event: tbot.logger.LogEvent) -> str:
        buf = ""

        last_newline = 0

        if not isinstance(self.channel, paramiko.Channel):
            raise Exception("Channel not initilized")

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
            raise Exception("Channel not initilized")

        self.channel.send(f"{command}\n")
        stdout = self._read_to_prompt(log_event)[len(command)+1:-len(self.prompt)]

        return stdout

    def _exec(self,
              command: str,
              log_event: tbot.logger.LogEvent) -> typing.Tuple[int, str]:
        log_event.prefix = "   >> "
        stdout = self._command(command, log_event)

        # Get the return code
        retcode = int(self._command("echo $?", None).strip())

        return retcode, stdout

    @property
    def unique_machine_name(self) -> str:
        """ Unique name of this machine, ``"board-rlogin-<boardshell-name>"`` """
        return f"board-rlogin-{self.name}"
