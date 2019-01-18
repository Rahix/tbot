import tbot
from selftest import *  # noqa
from uboot import build as uboot_build  # noqa


@tbot.testcase
def interactive_lab() -> None:
    """Start an interactive shell on the lab-host."""
    with tbot.acquire_lab() as lh:
        lh.interactive()


@tbot.testcase
def interactive_build() -> None:
    """Start an interactive shell on the build-host."""
    with tbot.acquire_lab() as lh:
        with lh.build() as bh:
            bh.exec0("cd", bh.workdir)
            bh.interactive()


@tbot.testcase
def interactive_board() -> None:
    """Start an interactive session on the selected boards serial console."""
    with tbot.acquire_lab() as lh:
        with tbot.acquire_board(lh) as b:
            b.channel.attach_interactive()


@tbot.testcase
def interactive_uboot() -> None:
    """Start an interactive U-Boot shell on the selected board."""
    with tbot.acquire_lab() as lh:
        with tbot.acquire_board(lh) as b:
            with tbot.acquire_uboot(b) as ub:
                ub.interactive()


@tbot.testcase
def interactive_linux() -> None:
    """Start an interactive Linux shell on the selected board."""
    with tbot.acquire_lab() as lh:
        with tbot.acquire_board(lh) as b:
            with tbot.acquire_linux(b) as lnx:
                lnx.interactive()
