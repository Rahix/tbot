"""
Interactive testcases for debugging & development
-------------------------------------------------
"""
import sys
import shutil
import time
import socket
import termios
import tty
import select
import typing
import paramiko
import tbot
from tbot import tc

# Based on https://github.com/paramiko/paramiko/blob/master/demos/interactive.py


# pylint: disable=too-many-branches, too-many-nested-blocks
def ishell(
    channel: paramiko.Channel,
    *,
    setup: typing.Optional[typing.Callable[[paramiko.Channel], None]] = None,
    abort: typing.Optional[str] = None,
) -> None:
    """
    An interactive shell

    :param paramiko.channel.Channel channel: Channel to use
    :param setup: An additional setup procedure to eg set a custom prompt
    :param str abort: A character that should not be sent to the remote but instead trigger
                  closing the interactive session
    """
    size = shutil.get_terminal_size()
    channel.resize_pty(size.columns, size.lines, 1000, 1000)
    if setup is not None:
        setup(channel)
    channel.send("\n")
    time.sleep(0.1)
    channel.recv(2)

    oldtty = termios.tcgetattr(sys.stdin)
    try:
        tty.setraw(sys.stdin.fileno())
        tty.setcbreak(sys.stdin.fileno())

        # Set to polling read
        mode = termios.tcgetattr(sys.stdin)
        special_chars = mode[6]
        if not isinstance(special_chars, list):
            raise tbot.TestcaseFailure("tcgetattr returned invalid mode")
        special_chars[termios.VMIN] = b"\0"
        special_chars[termios.VTIME] = b"\0"
        termios.tcsetattr(sys.stdin, termios.TCSAFLUSH, mode)

        channel.settimeout(0.0)

        while True:
            r, _, _ = select.select([channel, sys.stdin], [], [])
            if channel in r:
                try:
                    data = b""
                    fail_decode = True
                    while fail_decode:
                        data = data + channel.recv(1024)
                        try:
                            data_string = data.decode("utf-8")
                            fail_decode = False
                        except UnicodeDecodeError:
                            time.sleep(0.1)
                    if data == b"":
                        sys.stdout.write("\r\n*** Shell finished\r\n")
                        break
                    sys.stdout.write(data_string)
                    sys.stdout.flush()
                except socket.timeout:
                    pass
            if sys.stdin in r:
                data_string = sys.stdin.read(4096)
                if abort is not None and data_string == abort:
                    break
                if data_string == "":
                    break
                channel.send(data_string)
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, oldtty)
        channel.settimeout(None)


@tbot.testcase
def interactive_build_uboot(tb: tbot.TBot) -> None:
    """
    Open an interactive shell on the buildhost in the U-Boot builddir with
    the toolchain enabled.
    """
    tb.call("interactive_build", builddir=tb.config["uboot.builddir"])


@tbot.testcase
def interactive_build_linux(tb: tbot.TBot) -> None:
    """
    Open an interactive shell on the buildhost in the Linux builddir with
    the toolchain enabled.
    """
    tb.call("interactive_build", builddir=tb.config["linux.builddir"])


@tbot.testcase
def interactive_build(
    tb: tbot.TBot,
    *,
    builddir: typing.Optional[str] = None,
    toolchain: typing.Optional[tc.Toolchain] = None,
) -> None:
    """
    Open an interactive shell on the buildhost with the toolchain enabled.

    :param pathlib.PurePosixPath builddir: Where U-Boot is located, defaults to ``tb.config["uboot.builddir"]``
    :param Toolchain toolchain: Which toolchain to use, defaults to ``tb.config["board.toolchain"]``
    """

    ubbuilddir = builddir or ""
    toolchain = toolchain or tb.call("toolchain_get")

    @tb.call_then("toolchain_env", toolchain=toolchain)
    def interactive_shell(tb: tbot.TBot) -> None:  # pylint: disable=unused-variable
        """ Actual interactive shell """
        tb.shell.exec0(f"cd {tb.shell.workdir / ubbuilddir}")

        build_machine = tb.shell
        if not isinstance(build_machine, tbot.machine.MachineBuild):
            raise tbot.InvalidUsageException(
                "machine-build is not a MachineBuild, something is very wrong!"
            )
        channel = build_machine.channel

        def setup(ch: paramiko.Channel) -> None:
            """ Setup a custom prompt """
            # Set custom prompt
            ch.send(
                'PS1="\\[\\033[36m\\]U-Boot Build: \\[\\033[32m\\]\\w\\[\\033[0m\\]> "\n'
            )
            # Read back what we just sent
            time.sleep(0.1)
            ch.recv(1024)

        ishell(channel, setup=setup)


@tbot.testcase
def interactive_uboot(tb: tbot.TBot) -> None:
    """
    Open an interactive U-Boot prompt on the board
    """

    with tb.with_board_uboot() as tb:
        boardshell = tb.boardshell
        if not isinstance(boardshell, tbot.machine.MachineBoardUBoot):
            raise tbot.InvalidUsageException("boardshell is not a U-Boot machine")
        channel = boardshell.channel
        if not isinstance(channel, paramiko.Channel):
            raise tbot.InvalidUsageException("channel is not a paramiko channel")
        print("U-Boot Shell (CTRL-D to exit):")
        ishell(channel, abort="\x04")
        channel.send("\n")
        tbot.machine.shell_utils.read_to_prompt(channel, boardshell.prompt)
        print("\r")


@tbot.testcase
def interactive_linux(tb: tbot.TBot) -> None:
    """
    Open an interactive Linux prompt on the board
    """

    bname = tb.config["board.name"]
    with tb.with_board_linux() as tb:
        boardshell = tb.boardshell
        if not isinstance(boardshell, tbot.machine.MachineBoardLinux):
            raise tbot.InvalidUsageException("boardshell is not a Linux machine")
        channel = boardshell.channel
        if not isinstance(channel, paramiko.Channel):
            raise tbot.InvalidUsageException("channel is not a paramiko channel")

        def setup(ch: paramiko.Channel) -> None:
            """ Setup a custom prompt """
            # Set terminal size
            size = shutil.get_terminal_size()
            ch.send(f"stty cols {size.columns}\nstty rows {size.lines}\n$SHELL\n")
            # Set custom prompt
            ch.send(
                f'PS1="\\[\\033[36m\\]{bname}-linux: \\[\\033[32m\\]\\w\\[\\033[0m\\]> "\n'
            )
            # Read back what we just sent
            time.sleep(0.5)
            ch.recv(1024)

        print("Linux Shell (CTRL-D to exit):")
        ishell(channel, abort="\x04", setup=setup)
        channel.send("\x04")
        tbot.machine.shell_utils.read_to_prompt(channel, boardshell.prompt)
        print("\r")
