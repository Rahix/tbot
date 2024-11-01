import typing
import contextlib
import tbot
from tbot.machine import linux, board
from tbot.tc import uboot, git


def send(board: board.Board, repo: git.GitRepository) -> None:
    """Send a new U-Boot to the board, typically over USB."""
    sender: typing.Callable[[git.GitRepository], None] = getattr(board, "send")

    with tbot.testcase("uboot_send"):
        sender(repo)

@tbot.testcase
def uboot_build_and_send(
    lab: typing.Optional[tbot.selectable.LabHost] = None, clean: bool = True
) -> None:
    with lab or tbot.acquire_lab() as lh:
        # Build U-Boot
        with lh.build() as bh:
            with contextlib.ExitStack() as cx:
                repo = uboot.build(host=bh, clean=clean)
                with tbot.acquire_board(lh) as b:
                    send(b, repo)

@tbot.testcase
def uboot_build_send_interactive(
    lab: typing.Optional[tbot.selectable.LabHost] = None, clean: bool = True
) -> None:
    with lab or tbot.acquire_lab() as lh:
        # Build U-Boot
        with lh.build() as bh:
            with contextlib.ExitStack() as cx:
                repo = uboot.build(host=bh, clean=clean)
                with tbot.acquire_board(lh) as b:
                    send(b, repo)
                    b.interactive()
