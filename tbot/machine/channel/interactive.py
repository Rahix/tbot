import select
import sys
import termios
import tty
import typing

from .channel import Channel


def interactive_shell(
    channel: Channel,
    end_magic: typing.Optional[str] = None,
) -> None:
    oldtty = termios.tcgetattr(sys.stdin)
    try:
        tty.setraw(sys.stdin.fileno())
        tty.setcbreak(sys.stdin.fileno())

        mode = termios.tcgetattr(sys.stdin)
        special_chars = mode[6]
        assert isinstance(special_chars, list)
        special_chars[termios.VMIN] = b"\0"
        special_chars[termios.VTIME] = b"\0"
        termios.tcsetattr(sys.stdin, termios.TCSAFLUSH, mode)

        while True:
            r, _, _ = select.select([channel, sys.stdin], [], [])
            if channel in r:
                data_string = channel.recv()
                if data_string == end_magic:
                    break
                sys.stdout.write(data_string)
                sys.stdout.flush()
            if sys.stdin in r:
                data_string = sys.stdin.read(4096)
                if end_magic is None and data_string == "\x04":
                    break
                channel.send(data_string)
        sys.stdout.write("\r\n")
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, oldtty)
