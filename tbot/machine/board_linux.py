"""
Board machine for Linux interaction
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
"""
import pathlib
import random
import time
import typing
import paramiko
import tbot
from . import machine
from . import board
from . import shell_utils


# pylint: disable=too-many-instance-attributes
class MachineBoardLinux(board.MachineBoard):
    """ Board machine for Linux interaction

    :param str name: Name of the shell (eg ``someboard-bash``), defaults to
                 ``tb.config["linux.shell.name"]``
    :param str boardname: Name of the board, defaults to ``tb.config["board.name"]``
    :param str boot_command: U-Boot command to boot linux. May be multiple commands
                         separated by newlines, defaults to
                         ``tb.config["linux.boot_command"]``
    :param str login_prompt: The string to wait for before sending the username,
                         defaults to ``tb.config["linux.shell.login_prompt"]``
    :param float login_timeout: The time to wait after entering login credentials,
                          defaults to ``tb.config["linux.shell.login_timeout"]``
    :param str username: Username, defaults to ``tb.config["linux.shell.username"]``
    :param str password: Password, use ``""`` if no password is required,
                     defaults to ``tb.config["linux.shell.password"]``
    """
    # pylint: disable=too-many-arguments
    def __init__(
        self,
        *,
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

    def _setup(
        self, tb: "tbot.TBot", previous: typing.Optional[machine.Machine] = None
    ) -> "MachineBoardLinux":
        self.name = self.name or tb.config["board.serial.name", "unknown-linux"]
        # Check if the previous machine is also a MachineBoardUBoot,
        # if this is the case, prevent reinitialisation
        if (
            previous is not self
            and isinstance(previous, MachineBoardLinux)
            and previous.unique_machine_name == self.unique_machine_name
        ):
            return previous

        if isinstance(previous, tbot.machine.MachineBoardUBoot):
            self.ub_machine = previous
        else:
            # Create our own U-Boot
            ub_machine = tbot.machine.MachineBoardUBoot()
            # pylint: disable=protected-access
            self.ub_machine = ub_machine._setup(tb, previous)
            self.own_ub = True

        if not isinstance(self.ub_machine, tbot.machine.MachineBoardUBoot):
            raise Exception("Can't switch to linux if U-Boot is not yet present")

        self.powerup = False
        super()._setup(tb, previous)
        tbot.log.event(
            ty=["board", "boot-linux"],
            msg=f"{tbot.log.has_color('1')}LINUX BOOT{tbot.log.has_color('0')} ({self.boardname})",
            verbosity=tbot.log.Verbosity.INFO,
            dct={"board": self.boardname},
        )

        self.channel = self.ub_machine.channel
        if self.channel is None:
            raise Exception("U-Boot machine is not initialized correctly")

        self.boot_command = self.boot_command or tb.config["linux.boot_command"]
        self.login_prompt = (
            self.login_prompt or tb.config["linux.shell.login_prompt", "login: "]
        )
        self.login_timeout = (
            self.login_timeout or tb.config["linux.shell.login_timeout", 2]
        )
        self.username = self.username or tb.config["linux.shell.username", "root"]
        self.password = self.password or tb.config["linux.shell.password", ""]

        try:
            # Boot
            cmds = self.boot_command.split("\n")
            for cmd in cmds[:-1]:
                self.ub_machine.exec0(cmd)
            self.channel.send(f"{cmds[-1]}\n")
            stdout_handler = tbot.log_events.shell_command(
                machine=self.ub_machine.unique_machine_name.split("-"),
                command=cmds[-1],
                show=True,
                show_stdout=False,
            )
            stdout_handler.prefix = "   >> "

            boot_stdout = shell_utils.read_to_prompt(
                self.channel, self.login_prompt, stdout_handler
            )

            # Login
            self.channel.send(f"{self.username}\n")
            login_str = self.login_prompt + self.username
            stdout_handler.print(login_str)
            boot_stdout += login_str + "\n"
            time.sleep(0.2)
            self.channel.send(f"{self.password}\n")
            time.sleep(self.login_timeout)

            # Make linux aware of new terminal size
            self.channel.send("unset HISTFILE\nstty cols 200\nstty rows 200\nsh")

            # Set PROMPT
            self.prompt = f"TBOT-LINUX-{random.randint(11111,99999)}>"
            self.channel.send(
                f"\nunset HISTFILE\nPROMPT_COMMAND=\nPS1='{self.prompt}'\n"
            )
            boot_stdout += shell_utils.read_to_prompt(
                self.channel, self.prompt, stdout_handler
            )
            stdout_handler.dct["exit_code"] = 0
        except:  # noqa: E722
            # If anything goes wrong, turn off again
            self._destruct(tb)
            raise

        return self

    def _destruct(self, tb: "tbot.TBot") -> None:
        tbot.log.event(
            ty=["board", "linux-shutdown"],
            msg=f"{tbot.log.has_color('1')}LINUX SHUTDOWN{tbot.log.has_color('0')} ({self.boardname})",
            verbosity=tbot.log.Verbosity.INFO,
            dct={"board": self.boardname},
        )
        if isinstance(self.ub_machine, tbot.machine.MachineBoardUBoot):
            if self.own_ub:
                # pylint: disable=protected-access
                self.ub_machine._destruct(tb)
            else:
                # Reset to U-Boot
                self.ub_machine.powercycle()
        else:
            raise Exception(
                "U-Boot not initialized correctly, board might still be on!"
            )

    def _exec(
        self, command: str, stdout_handler: typing.Optional[tbot.log.LogStdoutHandler]
    ) -> typing.Tuple[int, str]:
        if isinstance(stdout_handler, tbot.log.LogStdoutHandler):
            stdout_handler.prefix = "   >< "
        return shell_utils.command_and_retval(
            self.channel, self.prompt, command, stdout_handler
        )

    @property
    def workdir(self) -> pathlib.PurePosixPath:
        return pathlib.PurePosixPath("/tmp")

    @property
    def unique_machine_name(self) -> str:
        """ Unique name of this machine, ``"board-linux-<boardshell-name>"`` """
        return f"board-linux-{self.name}"
