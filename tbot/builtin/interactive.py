"""
Interactive testcases for debugging
-----------------------------------
"""
import sys
import shutil
import time
import socket
import termios
import tty
import select
import typing
import pathlib
import paramiko
import tbot
from tbot import tc

# Based on https://github.com/paramiko/paramiko/blob/master/demos/interactive.py

#pylint: disable=too-many-branches, too-many-nested-blocks
def ishell(channel: paramiko.Channel, *,
           setup: typing.Optional[typing.Callable[[paramiko.Channel], None]] = None,
           abort: typing.Optional[str] = None,
          ) -> None:
    """
    An interactive shell

    :param setup: An additional setup procedure to eg set a custom prompt
    :param abort: A character that should not be sent to the remote but instead trigger
                  closing the interactive session
    :type abort: str
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
                        sys.stdout.write('\r\n*** Shell finished\r\n')
                        break
                    sys.stdout.write(data_string)
                    sys.stdout.flush()
                except socket.timeout:
                    pass
            if sys.stdin in r:
                data_string = sys.stdin.read(1)
                if abort is not None and data_string == abort:
                    break
                if data_string == "":
                    break
                channel.send(data_string)
                # TODO: Fix other data not being sent all at once
                # Send escape sequences all at once (fixes arrow keys)
                if data_string == "\x1B":
                    data_string = sys.stdin.read(2)
                    if data_string == "":
                        break
                    channel.send(data_string)
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, oldtty)

@tbot.testcase
@tbot.cmdline
def interactive_build(tb: tbot.TBot, *,
                      builddir: typing.Optional[pathlib.PurePosixPath] = None,
                      toolchain: typing.Optional[tc.Toolchain] = None,
                     ) -> None:
    """
    Open an interactive shell in the U-Boot build directory with the toolchain
    enabled.

    :param builddir: Where U-Boot is located, defaults to ``tb.config["uboot.builddir"]``
    :type builddir: pathlib.PurePosixPath
    :param toolchain: Which toolchain to use, defaults to ``tb.config["board.toolchain"]``
    :type toolchain: Toolchain
    """

    builddir = builddir or tb.config["uboot.builddir"]
    toolchain = toolchain or tb.call("toolchain_get")

    @tb.call_then("toolchain_env", toolchain=toolchain)
    def interactive_shell(tb: tbot.TBot) -> None: #pylint: disable=unused-variable
        """ Actual interactive shell """
        tb.shell.exec0(f"cd {builddir}")

        labhost_machine = tb.machines["labhost-env"]
        if not isinstance(labhost_machine, tbot.machine.MachineLabEnv):
            raise Exception("labhost-env is not a MachineLabEnv, something is very wrong!")
        channel = labhost_machine.channel
        def setup(ch: paramiko.Channel) -> None:
            """ Setup a custom prompt """
            # Set custom prompt
            ch.send("PS1=\"\\[\\033[36m\\]U-Boot Build: \\[\\033[32m\\]\\w\\[\\033[0m\\]> \"\n")
            # Read back what we just sent
            time.sleep(0.1)
            ch.recv(1024)
        ishell(channel, setup=setup)

@tbot.testcase
@tbot.cmdline
def interactive_uboot(tb: tbot.TBot) -> None:
    """
    Open an interactive U-Boot prompt on the board
    """

    with tb.with_board_uboot() as tb:
        boardshell = tb.boardshell
        if not isinstance(boardshell, tbot.machine.MachineBoardUBoot):
            raise Exception("boardshell is not a U-Boot machine")
        channel = boardshell.channel
        print("U-Boot Shell (CTRL-D to exit):")
        ishell(channel, abort="\x04")
        print("\r")

@tbot.testcase
@tbot.cmdline
def interactive_linux(tb: tbot.TBot) -> None:
    """
    Open an interactive Linux prompt on the board
    """

    bname = tb.config["board.name"]
    with tb.with_board_linux() as tb:
        boardshell = tb.boardshell
        if not isinstance(boardshell, tbot.machine.MachineBoardLinux):
            raise Exception("boardshell is not a Linux machine")
        channel = boardshell.channel
        def setup(ch: paramiko.Channel) -> None:
            """ Setup a custom prompt """
            # Set terminal size
            size = shutil.get_terminal_size()
            ch.send(f"stty cols {size.columns}\nstty rows {size.lines}\n$SHELL\n")
            # Set custom prompt
            ch.send(f"PS1=\"\\[\\033[36m\\]{bname}-linux: \\[\\033[32m\\]\\w\\[\\033[0m\\]> \"\n")
            # Read back what we just sent
            time.sleep(0.5)
            ch.recv(1024)
        print("Linux Shell (CTRL-D to exit):")
        ishell(channel, abort="\x04", setup=setup)
        print("\r")
