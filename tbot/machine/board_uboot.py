"""
Board machine for U-Boot interaction
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
"""
import random
import time
import typing
import paramiko
import tbot
from . import board

#pylint: disable=too-many-instance-attributes
class MachineBoardUBoot(board.MachineBoard):
    """ Board machine for U-Boot interaction

    :param name: Name of the shell (eg ``someboard-uboot``), defaults to
                 ``tb.config["board.shell.name"]``
    :type name: str
    :param boardname: Name of the board, defaults to ``tb.config["board.name"]``
    :type boardname: str
    :param power_cmd_on: Command to poweron the board, defaults to
                         ``tb.config["board.power.on_command"]``
    :type power_cmd_on: str
    :param power_cmd_off: Command to poweroff the board, defaults to
                          ``tb.config["board.power.off_command"]``
    :type power_cmd_off: str
    :param connect_command: Command to connect to the board with a tool that behaves similar
                            to rlogin, defaults to ``tb.config["board.shell.command"]``
    :type connect_command: str
    :param prompt: The U-Boot prompt that is expected on the board, defaults to
                   ``tb.config["board.shell.prompt"]`` or ``"U-Boot> "``
    :type prompt: str
    :param timeout: Time to wait before aborting autoboot (in seconds), defaults to
                    ``tb.config["board.shell.timeout"]`` or ``2`` seconds.
    :type timeout: float
    """
    #pylint: disable=too-many-arguments
    def __init__(self, *,
                 name: typing.Optional[str] = None,
                 boardname: typing.Optional[str] = None,
                 power_cmd_on: typing.Optional[str] = None,
                 power_cmd_off: typing.Optional[str] = None,
                 connect_command: typing.Optional[str] = None,
                 prompt: typing.Optional[str] = None,
                 timeout: typing.Optional[float] = None,
                ) -> None:
        super().__init__()
        self.name = name
        self.boardname = boardname

        self.power_cmd_on = power_cmd_on
        self.power_cmd_off = power_cmd_off
        self.connect_command = connect_command

        self.prompt = f"TBOT-BS-START-{random.randint(11111,99999)}>"
        self.uboot_prompt = prompt
        self.uboot_timeout = timeout

        self.channel: typing.Optional[paramiko.Channel] = None
        self.noenv: typing.Optional[tbot.machine.Machine] = None

    def _setup(self,
               tb: 'tbot.TBot',
               previous: 'typing.Optional[Machine]' = None,
              ) -> None:
        super()._setup(tb, previous)
        self.name = self.name or tb.config["board.shell.name", "unknown"]

        self.power_cmd_on = self.power_cmd_on or tb.config["board.power.on_command"]
        self.power_cmd_off = self.power_cmd_off or tb.config["board.power.off_command"]

        conn = tb.machines.connection
        self.channel = conn.get_transport().open_session()
        self.channel.get_pty("xterm-256color")

        # Resize the pty to ensure we do not get escape sequences from the terminal
        # trying to wrap to the next line
        self.channel.resize_pty(200, 200, 1000, 1000)
        self.channel.invoke_shell()

        self.connect_command = self.connect_command or tb.config["board.shell.command"]
        self.uboot_prompt = self.uboot_prompt or tb.config["board.shell.prompt", "U-Boot> "]
        self.uboot_timeout = self.uboot_timeout or tb.config["board.shell.timeout", 2]

        # Save the noenv shell to have it accessible later
        self.noenv = tb.machines["labhost-noenv"]

        try:
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
                verbosity=tbot.logger.Verbosity.INFO,
                dict_values={"log": boot_stdout})

            tb.log.log(ev)
        except: # If anything goes wrong, turn off again
            self._destruct(tb)
            raise

    def _destruct(self, tb: 'tbot.TBot') -> None:
        super()._destruct(tb)
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

        while True:
            # Read a lot and hope that this is all there is, so
            # we don't cut off inside a unicode sequence and fail
            # TODO: Make this more robust
            buf_data = self.channel.recv(10000000)
            try:
                buf_data = buf_data.decode("utf-8")
            except UnicodeDecodeError:
                print("===> FAILED UNICODE PARSING")
                print("buf: " + repr(buf))
                print("buf_data(raw): " + repr(buf_data))
                # TODO: Falling back to latin_1 is just a workaround as well ...
                buf_data = buf_data.decode("latin_1")
                print("buf_data(decoded): " + repr(buf_data))

            # Fix '\r's, replace '\r\n' twice to avoid some glitches
            buf_data = buf_data.replace('\r\n', '\n') \
                .replace('\r\n', '\n') \
                .replace('\r', '\n') \
                .replace('\0', '')

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
        """ Unique name of this machine, ``"board-uboot-<boardshell-name>"`` """
        return f"board-uboot-{self.name}"
