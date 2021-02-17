from typing import Iterator, Match

import pytest

import tbot
from tbot.machine import channel


@pytest.fixture
def ch() -> Iterator[channel.Channel]:
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

        raised = False
        try:
            ch.sendline("echo Illegal")
        except channel.ChannelBorrowedException:
            raised = True

        assert raised, "Borrow was unsuccessful"

    ch.sendline("echo back again")


def test_taking(ch: channel.Channel) -> None:
    ch.sendline("echo Hello")

    ch2 = ch.take()
    ch2.sendline("echo World")

    with pytest.raises(channel.ChannelTakenException):
        ch.sendline("echo Illegal")
