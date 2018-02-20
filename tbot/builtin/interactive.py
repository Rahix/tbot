import sys
import shutil
import time
import socket
import termios
import tty
import select
import paramiko
import tbot

#TODO: Credit paramiko example

@tbot.testcase
def interactive_build(tb: tbot.TBot, *,
                      builddir = None,
                      toolchain = None,
                      defconfig = None,
                     ):
    builddir = builddir or tb.config["uboot.builddir"]
    toolchain = toolchain or tb.config["board.toolchain"]
    defconfig = defconfig or tb.config["board.defconfig"]

    @tb.call_then("toolchain_env", toolchain=toolchain)
    def interactive_shell(tb: tbot.TBot) -> None: #pylint: disable=unused-variable
        tb.shell.exec0(f"cd {builddir}")

        channel = tb.machines["labhost-env"].channel
        size = shutil.get_terminal_size()
        channel.resize_pty(size.columns, size.lines, 1000, 1000)
        channel.send("PS1=\"\\[\\033[36m\\]U-Boot Build: \\[\\033[32m\\]\\w\\[\\033[0m\\]> \"\n")
        # Read back what we just sent
        time.sleep(0.1)
        channel.recv(1024)
        channel.send("\n")
        time.sleep(0.1)
        channel.recv(2)

        oldtty = termios.tcgetattr(sys.stdin)
        try:
            tty.setraw(sys.stdin.fileno())
            tty.setcbreak(sys.stdin.fileno())
            channel.settimeout(0.0)

            while True:
                r, w, e = select.select([channel, sys.stdin], [], [])
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
                        if len(data) == 0:
                            sys.stdout.write('\r\n*** Shell finished\r\n')
                            break
                        sys.stdout.write(data_string)
                        sys.stdout.flush()
                    except socket.timeout:
                        pass
                if sys.stdin in r:
                    data = sys.stdin.read(1)
                    if len(data) == 0:
                        break
                    channel.send(data)
                    # TODO: Fix other data not being sent all at once
                    # Send escape sequences all at once (fixes arrow keys)
                    if data == "\x1B":
                        data = sys.stdin.read(2)
                        if len(data) == 0:
                            break
                        channel.send(data)
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, oldtty)
