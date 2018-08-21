import tbot
from selftest import *  # noqa


@tbot.testcase
def interactive_lab() -> None:
    with tbot.acquire_lab() as lh:
        lh.interactive()


@tbot.testcase
def interactive_build() -> None:
    with tbot.acquire_lab() as lh:
        with lh.default_build() as bh:
            bh.interactive()
