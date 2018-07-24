"""
Board machine for U-Boot interaction
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
"""
import random
import typing
import pathlib
import time
import paramiko
import tbot
from . import machine
from . import board
from . import shell_utils


# pylint: disable=too-many-instance-attributes
class MachineBoardUBoot(board.MachineBoard):
    """ Board machine for U-Boot interaction

    :param str name: Name of the shell (eg ``someboard-uboot``), defaults to
                 ``tb.config["board.serial.name"]``
    :param str boardname: Name of the board, defaults to ``tb.config["board.name"]``
    :param str power_cmd_on: Command to poweron the board, defaults to
                         ``tb.config["board.power.on_command"]``
    :param str power_cmd_off: Command to poweroff the board, defaults to
                          ``tb.config["board.power.off_command"]``
    :param str connect_command: Command to connect to the board with a tool that behaves similar
                            to rlogin, defaults to ``tb.config["board.serial.command"]``
    :param str autoboot_prompt: The U-Boot autoboot prompt that is expected on the board, defaults to
            ``tb.config["uboot.shell.autoboot-prompt"]`` or ``"Hit any key to stop autoboot: <x> "``
            (interpreted as a regular expression)
    :param str autoboot_keys: The key sequence to stop autoboot, defaults to
                              ``tb.config["uboot.shell.autoboot-keys"]`` or ``"\\n"``
    :param str prompt: The U-Boot prompt that is expected on the board, defaults to
                   ``tb.config["uboot.shell.prompt"]`` or ``"U-Boot> "``
    """
    # pylint: disable=too-many-arguments
    def __init__(
        self,
        *,
        name: typing.Optional[str] = None,
        boardname: typing.Optional[str] = None,
        power_cmd_on: typing.Optional[str] = None,
        power_cmd_off: typing.Optional[str] = None,
        connect_command: typing.Optional[str] = None,
        autoboot_prompt: typing.Optional[str] = None,
        autoboot_keys: typing.Optional[str] = None,
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
        self.autoboot_keys = autoboot_keys
        self.uboot_prompt = prompt

        self.channel: typing.Optional[paramiko.Channel] = None
        self.conn: typing.Optional[paramiko.SSHClient] = None
        self.noenv: typing.Optional[tbot.machine.Machine] = None

    def _setup(
        self, tb: "tbot.TBot", previous: typing.Optional[machine.Machine] = None
    ) -> "MachineBoardUBoot":
        self.name = self.name or tb.config["board.serial.name", "unknown"]
        # Check if the previous machine is also a MachineBoardUBoot,
        # if this is the case, prevent reinitialisation
        if (
            previous is not self
            and isinstance(previous, MachineBoardUBoot)
            and previous.unique_machine_name == self.unique_machine_name
        ):
            return previous

        super()._setup(tb, previous)

        self.power_cmd_on = self.power_cmd_on or tb.config["board.power.on_command"]
        self.power_cmd_off = self.power_cmd_off or tb.config["board.power.off_command"]

        conn = tb.machines.connection
        self.conn = conn
        self.channel = conn.get_transport().open_session()
        shell_utils.setup_channel(self.channel, self.prompt)

        self.connect_command = self.connect_command or tb.config["board.serial.command"]
        self.autoboot_prompt = (
            self.autoboot_prompt
            or tb.config[
                "uboot.shell.autoboot-prompt", r"Hit any key to stop autoboot:\s+\d+\s+"
            ]
        )
        self.autoboot_keys = (
            self.autoboot_keys or tb.config["uboot.shell.autoboot-keys", "\n"]
        )
        self.uboot_prompt = (
            self.uboot_prompt or tb.config["uboot.shell.prompt", "U-Boot> "]
        )

        # Save the noenv shell to have it accessible later
        self.noenv = tb.machines["labhost-noenv"]

        if self.noenv is None:
            raise tbot.InvalidUsageException("no-env shell does not exist")

        try:
            # Poweron the board
            self.channel.send(f"{self.connect_command}\n")
            # Small timeout to hopefully fix boards booting too fast
            time.sleep(tb.config["board.serial.connect_wait_time", 0.5])

            self.noenv.exec0(self.power_cmd_on, log_show_stdout=False)

            stdout_handler = tbot.log.event(
                ty=["board", "boot"],
                msg=f"(labhost, preboot) {repr(self.connect_command)[1:-1]}",
                verbosity=tbot.log.Verbosity.VERY_VERBOSE,
                dct={"log": ""},
            )
            stdout_handler.prefix = "   <> "
            stdout_handler.is_continuation = True
            # Stop autoboot
            boot_stdout = shell_utils.read_to_prompt(
                self.channel,
                self.autoboot_prompt,
                prompt_regex=True,
                stdout_handler=stdout_handler,
            )
            self.channel.send(self.autoboot_keys)
            self.prompt = self.uboot_prompt
            boot_stdout += shell_utils.read_to_prompt(self.channel, self.prompt)
        except:  # noqa: E722
            # If anything goes wrong, turn off again
            self._destruct(tb)
            raise

        return self

    def _destruct(self, tb: "tbot.TBot") -> None:
        super()._destruct(tb)
        if (
            isinstance(self.noenv, tbot.machine.Machine)
            and self.power_cmd_off is not None
        ):
            self.noenv.exec0(self.power_cmd_off, log_show_stdout=False)
        else:
            raise Exception(
                "noenv shell not initialized correctly, board might still be on!"
            )
        if isinstance(self.channel, paramiko.Channel):
            self.channel.close()
        else:
            raise tbot.InvalidUsageException("Channel not initilized")

    def _exec(
        self, command: str, stdout_handler: typing.Optional[tbot.log.LogStdoutHandler]
    ) -> typing.Tuple[int, str]:
        if isinstance(stdout_handler, tbot.log.LogStdoutHandler):
            stdout_handler.prefix = "   >> "
        return shell_utils.command_and_retval(
            self.channel, self.prompt, command, stdout_handler
        )

    @property
    def workdir(self) -> pathlib.PurePosixPath:
        raise tbot.InvalidUsageException("UBoot does not have a workdir")

    @property
    def unique_machine_name(self) -> str:
        """ Unique name of this machine, ``"board-uboot-<boardshell-name>"`` """
        return f"board-uboot-{self.name}"
