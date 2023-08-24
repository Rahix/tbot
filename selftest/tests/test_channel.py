from typing import Iterator, Match

import pytest

import tbot
from tbot.machine import board, channel, connector


@pytest.fixture
def ch() -> Iterator[channel.Channel]:
    with tbot.log.with_verbosity(tbot.log.Verbosity.CHANNEL):
        with channel.SubprocessChannel() as ch:
            ch.read()

            # We must ensure that nothing enters the history from the commands sent
            # in the following tests.
            ch.sendline("unset HISTFILE", read_back=True)
            ch.read()

            yield ch


def test_simple_command(ch: channel.Channel) -> None:
    ch.sendline("echo Hello World", read_back=True)
    out = ch.read()
    assert out.startswith(b"Hello World")


def test_simple_reading(ch: channel.Channel) -> None:
    ch.write(b"1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    out = ch.read(10)
    assert out == b"1234567890"

    out = ch.read()
    assert out == b"ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def test_simple_read_iter(ch: channel.Channel) -> None:
    ch.write(b"12345678901234567890")
    final = bytearray()
    for new in ch.read_iter(10):
        final.extend(new)
    assert final == b"1234567890"
    for i in range(1, 10):
        c = ch.read(1)
        assert c == str(i).encode("utf-8")


def test_simple_readline(ch: channel.Channel) -> None:
    ch.sendline("echo Hello; echo World", read_back=True)
    out_s = ch.readline()
    assert out_s == "Hello\n"
    out_s = ch.readline()
    assert out_s == "World\n"


def test_simple_expect(ch: channel.Channel) -> None:
    ch.sendline("echo Lorem Ipsum")
    res = ch.expect(["Lol", "Ip"])
    assert res.i == 1
    assert res.match == "Ip"


def test_simple_expect2(ch: channel.Channel) -> None:
    ch.sendline("echo Lorem Ipsum Dolor Sit")
    res = ch.expect(["Lol", "Dolor", "Dol"])
    assert res.i == 1
    assert res.match == "Dolor"


def test_simple_expect3(ch: channel.Channel) -> None:
    ch.sendline("echo Lo1337rem")
    res = ch.expect(["Dolor", "roloD", tbot.Re(r"Lo(\d{1,20})"), "rem"])
    assert res.i == 2
    assert isinstance(res.match, Match), "Not a match object"
    assert res.match.group(1) == b"1337"


def test_borrowing(ch: channel.Channel) -> None:
    ch.sendline("echo Hello")

    with ch.borrow() as ch2:
        ch2.sendline("echo World")

        with pytest.raises(tbot.error.ChannelBorrowedError):
            ch.sendline("echo Illegal")

    ch.sendline("echo back again")


def test_taking(ch: channel.Channel) -> None:
    ch.sendline("echo Hello")

    ch2 = ch.take()
    ch2.sendline("echo World")

    with pytest.raises(tbot.error.ChannelTakenError):
        ch.sendline("echo Illegal")


def test_termination(ch: channel.Channel) -> None:
    ch.sendline("exit")
    with pytest.raises(tbot.error.ChannelClosedError):
        ch.read_until_timeout(5)


def test_unbounded_pattern(ch: channel.Channel) -> None:
    """
    Check that an unbounded pattern is detected properly.
    """
    ub_pat = tbot.Re("unbounded$ .*")
    with pytest.raises(Exception, match="not bounded"):
        ch.read_until_prompt(prompt=ub_pat, timeout=1)


def test_blacklist(ch: channel.Channel) -> None:
    """
    Test whether blacklisted characters are properly caught.
    """
    ch._write_blacklist = [
        0x03,  # ETX  | End of Text / Interrupt
        0x04,  # EOT  | End of Transmission
        0x11,  # DC1  | Device Control One (XON)
        0x12,  # DC2  | Device Control Two
        0x13,  # DC3  | Device Control Three (XOFF)
        0x14,  # DC4  | Device Control Four
        0x15,  # NAK  | Negative Acknowledge
        0x16,  # SYN  | Synchronous Idle
        0x17,  # ETB  | End of Transmission Block
        0x1A,  # SUB  | Substitute / Suspend Process
        0x1C,  # FS   | File Separator
        0x7F,  # DEL  | Delete
        0x20,  # For test purposes: Space is illegal
    ]
    with pytest.raises(tbot.error.IllegalDataException):
        ch.sendline(" ")


def test_slowsend_channel(ch: channel.Channel) -> None:
    ch.slow_send_delay = 0.1
    ch.slow_send_chunksize = 2

    # from test_simple_expect3
    ch.sendline("echo Lo1337rem")
    res = ch.expect(["Dolor", "roloD", tbot.Re(r"Lo(\d{1,20})"), "rem"])
    assert res.i == 2
    assert isinstance(res.match, Match), "Not a match object"
    assert res.match.group(1) == b"1337"


def test_nullchannel_machine() -> None:
    """
    Ensure that we can instanciate a machine with a null channel properly.
    """

    class NullChannelMachine(connector.NullConnector, board.Board):
        pass

    with NullChannelMachine() as m:
        assert not m.ch.closed

    assert m.ch.closed
