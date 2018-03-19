"""
Board machine for Linux interaction
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
"""
import random
import time
import typing
import paramiko
import tbot
from . import machine
from . import board

#pylint: disable=too-many-instance-attributes
class MachineBoardLinux(board.MachineBoard):
    """ Board machine for Linux interaction

    :param name: Name of the shell (eg ``someboard-bash``), defaults to
                 ``tb.config["linux.shell.name"]``
    :type name: str
    :param boardname: Name of the board, defaults to ``tb.config["board.name"]``
    :type boardname: str
    :param boot_command: U-Boot command to boot linux. May be multiple commands
                         separated by newlines, defaults to
                         ``tb.config["linux.boot_command"]``
    :type boot_command: str
    :param login_prompt: The string to wait for before sending the username,
                         defaults to ``tb.config["linux.shell.login_prompt"]``
    :type login_prompt: str
    :param login_timeout: The time to wait after entering login credentials,
                          defaults to ``tb.config["linux.shell.login_timeout"]``
    :type login_timeout: float
    :param username: Username, defaults to ``tb.config["linux.shell.username"]``
    :type username: str
    :param password: Password, use ``""`` if no password is required,
                     defaults to ``tb.config["linux.shell.password"]``
    :type password: str
    """
    #pylint: disable=too-many-arguments
    def __init__(self, *,
                 name: typing.Optional[str] = None,
                 boardname: typing.Optional[str] = None,
                 boot_command: typing.Optional[str] = None,
                 login_prompt: typing.Optional[str] = None,
                 login_timeout: typing.Optional[float] = None,
                 username: typing.Optional[str] = None,
                 password: typing.Optional[str] = None,
                ) -> None:
        super().__init__()
        self.name = name
        self.boardname = boardname

        self.boot_command = boot_command

        self.prompt = f"TBOT-LINUX-{random.randint(11111,99999)}>"
        self.login_prompt = login_prompt
        self.login_timeout = login_timeout
        self.username = username
        self.password = password

        self.channel: typing.Optional[paramiko.Channel] = None
        self.ub_machine: typing.Optional[tbot.machine.MachineBoardUBoot] = None
        self.own_ub = False

    def _setup(self,
               tb: 'tbot.TBot',
               previous: typing.Optional[machine.Machine] = None,
              ) -> 'MachineBoardLinux':
        self.name = self.name or tb.config["board.serial.name", "unknown-linux"]
        # Check if the previous machine is also a MachineBoardUBoot,
        # if this is the case, prevent reinitialisation
        if previous is not self and \
            isinstance(previous, MachineBoardLinux) and \
            previous.unique_machine_name == self.unique_machine_name:
            return previous

        if isinstance(previous, tbot.machine.MachineBoardUBoot):
            self.ub_machine = previous
        else:
            # Create our own U-Boot
            ub_machine = tbot.machine.MachineBoardUBoot()
            #pylint: disable=protected-access
            self.ub_machine = ub_machine._setup(tb, previous)
            self.own_ub = True

        if not isinstance(self.ub_machine, tbot.machine.MachineBoardUBoot):
            raise Exception("Can't switch to linux if U-Boot is not yet present")

        self.powerup = False
        super()._setup(tb, previous)
        ev = tbot.logger.CustomLogEvent(
            ["board", "boot-linux"],
            stdout=f"\x1B[1mLINUX BOOT\x1B[0m ({self.boardname})",
            verbosity=tbot.logger.Verbosity.INFO,
            dict_values={"board": self.boardname})
        tb.log.log(ev)

        self.channel = self.ub_machine.channel

        self.boot_command = self.boot_command or tb.config["linux.boot_command"]
        self.login_prompt = self.login_prompt or tb.config["linux.shell.login_prompt", "login: "]
        self.login_timeout = self.login_timeout or tb.config["linux.shell.login_timeout", 2]
        self.username = self.username or tb.config["linux.shell.username", "root"]
        self.password = self.password or tb.config["linux.shell.password", ""]

        try:
            # Boot
            cmds = self.boot_command.split('\n')
            for cmd in cmds[:-1]:
                self.ub_machine.exec0(cmd)
            self.channel.send(f"{cmds[-1]}\n")
            ev = tbot.logger.ShellCommandLogEvent(self.ub_machine.unique_machine_name.split('-'),
                                                  cmds[-1], prefix="   >> ",
                                                  log_show_stdout=False)
            tb.log.log(ev)
            self.prompt = self.login_prompt
            boot_stdout = self._read_to_prompt(ev)

            # Login
            self.channel.send(f"{self.username}\n")
            login_str = self.login_prompt + self.username
            ev.add_line(login_str)
            boot_stdout += login_str + "\n"
            time.sleep(0.2)
            self.channel.send(f"{self.password}\n")
            time.sleep(self.login_timeout)

            # Make linux aware of new terminal size
            self.channel.send("stty cols 200\nstty rows 200\nsh")

            # Set PROMPT
            self.prompt = f"TBOT-LINUX-{random.randint(11111,99999)}>"
            self.channel.send(f"\nPROMPT_COMMAND=\nPS1='{self.prompt}'\n")
            boot_stdout += self._read_to_prompt(ev)
            ev.finished(0)
        except: # If anything goes wrong, turn off again
            self._destruct(tb)
            raise

        return self

    def _destruct(self, tb: 'tbot.TBot') -> None:
        ev = tbot.logger.CustomLogEvent(
            ["board", "linux-shutdown"],
            stdout=f"\x1B[1mLINUX SHUTDOWN\x1B[0m ({self.boardname})",
            verbosity=tbot.logger.Verbosity.INFO,
            dict_values={"board": self.boardname})
        tb.log.log(ev)
        if isinstance(self.ub_machine, tbot.machine.MachineBoardUBoot):
            if self.own_ub:
                #pylint: disable=protected-access
                self.ub_machine._destruct(tb)
            else:
                # Reset to U-Boot
                self.ub_machine.powercycle()
        else:
            raise Exception("U-Boot not initialized correctly, board might still be on!")

    def _read_to_prompt(self, log_event: tbot.logger.LogEvent) -> str:
        buf = ""

        last_newline = 0

        if not isinstance(self.channel, paramiko.Channel):
            raise Exception("Channel not initilized")

        while True:
            # Read a lot and hope that this is all there is, so
            # we don't cut off inside a unicode sequence and fail
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
        log_event.prefix = "   >< "
        stdout = self._command(command, log_event)

        # Get the return code
        retcode = int(self._command("echo $?", None).strip())

        return retcode, stdout

    @property
    def unique_machine_name(self) -> str:
        """ Unique name of this machine, ``"board-linux-<boardshell-name>"`` """
        return f"board-linux-{self.name}"
