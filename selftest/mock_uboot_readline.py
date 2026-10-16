"""
Mock of a U-Boot console built without CONFIG_CMDLINE_EDITING.

U-Boot then reads the command line with the simple readline of
common/cli_readline.c.  It echoes every typed character itself and answers
the Enter key with puts("\\r\\n").  The serial uclass puts a \r in front of
every \n it sends, so the echo of the Enter key is "\\r\\r\\n" (with
CONFIG_CMDLINE_EDITING it is "\\r\\n").

Only the commands the selftest needs are implemented.
"""

import os
import shlex
import tty
import typing


def puts(s: str) -> None:
    # The serial uclass sends "\r\n" for every "\n".
    os.write(1, s.replace("\n", "\r\n").encode("utf-8"))


def readline() -> typing.Optional[str]:
    line = bytearray()
    while True:
        c = os.read(0, 1)
        if c == b"":
            raise EOFError
        if c in (b"\r", b"\n"):
            puts("\r\n")
            return line.decode("utf-8")
        if c == b"\x03":
            # ^C discards the input, see common/cli_readline.c
            return None
        os.write(1, c)
        line += c


def main() -> None:
    tty.setraw(0)
    env = {}
    retcode = 0
    while True:
        puts("=> ")
        try:
            line = readline()
        except EOFError:
            return
        if line is None:
            # common/cli_simple.c
            puts("<INTERRUPT>\n")
            continue
        args = shlex.split(line)
        if not args:
            continue

        cmd = args[0]
        if args == ["echo", "$?"]:
            puts(f"{retcode}\n")
            continue
        retcode = 0
        if cmd == "echo":
            puts(" ".join(args[1:]) + "\n")
        elif cmd == "setenv":
            if len(args) > 2:
                env[args[1]] = " ".join(args[2:])
            else:
                env.pop(args[1], None)
        elif cmd == "printenv":
            for var in args[1:]:
                if var in env:
                    puts(f"{var}={env[var]}\n")
                else:
                    puts('## Error: "' + var + '" not defined\n')
                    retcode = 1
        elif cmd == "true":
            pass
        elif cmd == "false":
            retcode = 1
        else:
            puts("Unknown command '" + cmd + "' - try 'help'\n")
            retcode = 1


if __name__ == "__main__":
    main()
