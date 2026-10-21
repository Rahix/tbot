import re
import typing

import pytest

from tbot.machine.channel.channel import BoundedPattern
from tbot.machine.linux import util

ESC = b"\x1b"
END = b"INTERACTIVE-END-7c6b27e74b439292c07b917241686a7f"


def found_at(pattern: "re.Pattern[bytes]", chunks: typing.List[bytes]) -> int:
    """index of the chunk after which read_until_prompt() finds the prompt"""
    # read_until_prompt() anchors the pattern at the end of what it has read
    anchored = re.compile(pattern.pattern + b"$", pattern.flags)
    buf = b""
    for i, chunk in enumerate(chunks):
        buf += chunk
        if anchored.search(buf) is not None:
            return i
    return -1


# a board with ash: the echo of the PS1 line ends a read right after "> "
ASH_CHUNKS = [
    b"ash\r\n033[36m\\]board-linux: \\[\\033[32m\\]\\w\\[\\033[0m\\]> ",
    b"'\r\n",
    b"\r\n",
    END + b"PS1='\\[\\033[36m\\]board-linux: \\[\\033[32m\\]\\w\\[\\033[0m\\]> '\r\n",
    ESC + b"[36mboard-linux: " + ESC + b"[32m~" + ESC + b"[0m> ",
]

# a board with bash, whose new shell shows the end marker as its prompt
# until PS1 is set, and an escape sequence after the prompt
BASH_CHUNKS = [
    b"bash --norc --noprofile\r\n"
    b"PS1='\\[\\033[36m\\]board-linux: \\[\\033[32m\\]\\w\\[\\033[0m\\]> ",
    b"'\r\n",
    END + b"set -o emacs\r\n",
    END + b"PS1='\\[\\033[36m\\]board-linux: \\[\\033[32m\\]\\w\\[\\033[0m\\]> '\r\n",
    ESC + b"[",
    b"36mboard-linux: " + ESC + b"[32m~" + ESC + b"[0m> " + ESC + b"[K",
]

PLAIN_CHUNKS = [
    b"ash\r\nPS1='board-linux> ",
    b"'\r\n",
    END + b"PS1='board-linux> '\r\n",
    b"board-linux> ",
]


@pytest.mark.parametrize("chunks", [ASH_CHUNKS, BASH_CHUNKS])  # type: ignore
def test_colored_prompt_not_in_echo(chunks: typing.List[bytes]) -> None:
    _, pattern = util.interactive_prompt("board-linux", False)
    assert found_at(pattern, chunks) == len(chunks) - 1


def test_plain_prompt_not_in_echo() -> None:
    _, pattern = util.interactive_prompt("board-linux", True)
    assert found_at(pattern, PLAIN_CHUNKS) == len(PLAIN_CHUNKS) - 1


def test_old_pattern_matched_the_echo() -> None:
    """the pattern before stopped in the echo, the end marker came after"""
    old = re.compile(b"> (\x1B\\[.{0,10})?")
    assert found_at(old, BASH_CHUNKS) == 0


def test_ps1() -> None:
    assert util.interactive_prompt("lab", True)[0] == "lab> "
    assert (
        util.interactive_prompt("lab", False)[0]
        == "\\[\\033[36m\\]lab: \\[\\033[32m\\]\\w\\[\\033[0m\\]> "
    )


@pytest.mark.parametrize("plain", [False, True])  # type: ignore
def test_pattern_is_bounded(plain: bool) -> None:
    """read_until_prompt() needs a pattern of bounded length"""
    assert len(BoundedPattern(util.interactive_prompt("board-linux", plain)[1])) > 0
