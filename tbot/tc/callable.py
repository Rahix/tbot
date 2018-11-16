import tbot
from selftest import *  # noqa
from uboot import build as uboot_build  # noqa


@tbot.testcase
def interactive_lab() -> None:
    with tbot.acquire_lab() as lh:
        lh.interactive()


@tbot.testcase
def interactive_build() -> None:
    with tbot.acquire_lab() as lh:
        with lh.default_build() as bh:
            bh.interactive()


@tbot.testcase
def interactive_board() -> None:
    with tbot.acquire_lab() as lh:
        with tbot.acquire_board(lh) as b:
            b.channel.attach_interactive()


@tbot.testcase
def interactive_uboot() -> None:
    with tbot.acquire_lab() as lh:
        with tbot.acquire_board(lh) as b:
            with tbot.acquire_uboot(b) as ub:
                ub.interactive()


@tbot.testcase
def interactive_linux() -> None:
    with tbot.acquire_lab() as lh:
        with tbot.acquire_board(lh) as b:
            with tbot.acquire_linux(b) as lnx:
                lnx.interactive()
