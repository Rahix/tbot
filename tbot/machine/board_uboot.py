"""
Board machine for U-Boot interaction
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
"""
import random
import typing
import paramiko
import tbot
from . import machine
from . import board
from . import shell_utils

#pylint: disable=too-many-instance-attributes
class MachineBoardUBoot(board.MachineBoard):
    """ Board machine for U-Boot interaction

    :param name: Name of the shell (eg ``someboard-uboot``), defaults to
                 ``tb.config["board.serial.name"]``
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
                            to rlogin, defaults to ``tb.config["board.serial.command"]``
    :type connect_command: str
    :param autoboot_prompt: The U-Boot autoboot prompt that is expected on the board, defaults to
            ``tb.config["uboot.shell.autoboot-prompt"]`` or ``"Hit any key to stop autoboot: <x> "``
            (interpreted as a regular expression)
    :type autoboot_prompt: str
    :param prompt: The U-Boot prompt that is expected on the board, defaults to
                   ``tb.config["uboot.shell.prompt"]`` or ``"U-Boot> "``
    :type prompt: str
    """
    #pylint: disable=too-many-arguments
    def __init__(self, *,
                 name: typing.Optional[str] = None,
                 boardname: typing.Optional[str] = None,
                 power_cmd_on: typing.Optional[str] = None,
                 power_cmd_off: typing.Optional[str] = None,
                 connect_command: typing.Optional[str] = None,
                 autoboot_prompt: typing.Optional[str] = None,
                 prompt: typing.Optional[str] = None,
                ) -> None:
        super().__init__()
        self.name = name
        self.boardname = boardname

        self.power_cmd_on = power_cmd_on
        self.power_cmd_off = power_cmd_off
        self.connect_command = connect_command

        self.prompt = f"TBOT-BS-START-{random.randint(11111,99999)}>"
        self.autoboot_prompt = autoboot_prompt
        self.uboot_prompt = prompt

        self.channel: typing.Optional[paramiko.Channel] = None
        self.conn: typing.Optional[paramiko.SSHClient] = None
        self.noenv: typing.Optional[tbot.machine.Machine] = None

    def _setup(self,
               tb: 'tbot.TBot',
               previous: typing.Optional[machine.Machine] = None,
              ) -> 'MachineBoardUBoot':
        self.name = self.name or tb.config["board.serial.name", "unknown"]
        # Check if the previous machine is also a MachineBoardUBoot,
        # if this is the case, prevent reinitialisation
        if previous is not self and \
            isinstance(previous, MachineBoardUBoot) and \
            previous.unique_machine_name == self.unique_machine_name:
            return previous

        super()._setup(tb, previous)

        self.power_cmd_on = self.power_cmd_on or tb.config["board.power.on_command"]
        self.power_cmd_off = self.power_cmd_off or tb.config["board.power.off_command"]

        conn = tb.machines.connection
        self.conn = conn
        self.channel = conn.get_transport().open_session()
        shell_utils.setup_channel(self.channel, self.prompt)

        self.connect_command = self.connect_command or tb.config["board.serial.command"]
        self.autoboot_prompt = self.autoboot_prompt or \
            tb.config["uboot.shell.autoboot-prompt", r"Hit any key to stop autoboot:\s+\d+\s+"]
        self.uboot_prompt = self.uboot_prompt or tb.config["uboot.shell.prompt", "U-Boot> "]

        # Save the noenv shell to have it accessible later
        self.noenv = tb.machines["labhost-noenv"]

        try:
            # Poweron the board
            self.channel.send(f"{self.connect_command}\n")

            self.noenv.exec0(self.power_cmd_on, log_show_stdout=False)

            stdout_handler = tbot.log.event(
                ty=["board", "boot"],
                msg=f"(labhost, preboot) {repr(self.connect_command)[1:-1]}",
                verbosity=tbot.log.Verbosity.INFO,
                dct={"log": ""},
            )
            stdout_handler.reset_verbosity(tbot.log.Verbosity.VERY_VERBOSE)
            stdout_handler.prefix = "   <> "
            stdout_handler.is_continuation = True
            # Stop autoboot
            boot_stdout = shell_utils.read_to_prompt(self.channel,
                                                     self.autoboot_prompt,
                                                     prompt_regex=True,
                                                     stdout_handler=stdout_handler)
            self.channel.send("\n")
            self.prompt = self.uboot_prompt
            boot_stdout += shell_utils.read_to_prompt(self.channel, self.prompt)

        except: # If anything goes wrong, turn off again
            self._destruct(tb)
            raise

        return self

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

    def _exec(self,
              command: str,
              stdout_handler) -> typing.Tuple[int, str]:
        stdout_handler.prefix = "   >> "
        return shell_utils.command_and_retval(
            self.channel,
            self.prompt,
            command,
            stdout_handler
        )

    @property
    def unique_machine_name(self) -> str:
        """ Unique name of this machine, ``"board-uboot-<boardshell-name>"`` """
        return f"board-uboot-{self.name}"
