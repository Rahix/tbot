import typing
import contextlib
import tbot
from tbot.machine import linux, board
from tbot.tc import uboot, git


def safe_flash(board: board.Board, repo: git.GitRepository) -> None:
    """Flash but drop into shell on failure (if -f safe)."""
    flasher: typing.Callable[[git.GitRepository], None] = getattr(board, "flash")

    with tbot.testcase("uboot_flash"):
        flasher(repo)

@tbot.testcase
def uboot_build_and_flash(
    lab: typing.Optional[tbot.selectable.LabHost] = None,
    clean: bool = True,
    rev: typing.Optional[str] = None,
    patch: typing.Optional[linux.Path] = None,
) -> None:
    with lab or tbot.acquire_lab() as lh:
        # Build U-Boot
        with lh.build() as bh:
            with contextlib.ExitStack() as cx:
                b = cx.enter_context(tbot.acquire_board(lh))
                repo = uboot.build(host=bh, clean=clean, rev=rev, patch=patch)
                #ub = cx.enter_context(tbot.acquire_uboot(b))

                safe_flash(b, repo)
            """
            # Reboot and check version
            with tbot.testcase("uboot_check_version"), contextlib.ExitStack() as cx:
                b = cx.enter_context(tbot.acquire_board(lh))
                ub = cx.enter_context(tbot.acquire_uboot(b))

                vers = ub.exec0("version").split("\n")[0]
                tbot.log.message(f"Found version '{vers}' on hardware")

                strings = bh.exec0(
                    "strings",
                    repo / "u-boot.bin",
                    linux.Pipe,
                    "/usr/bin/grep",
                    "U-Boot",
                ).strip()

                assert vers in strings, "U-Boot version does not seem to match!"
            """


@tbot.testcase
def uboot_bare_flash(lab: typing.Optional[tbot.selectable.LabHost] = None,) -> None:
    with lab or tbot.acquire_lab() as lh:
        with lh.build() as bh:
            repo = uboot.checkout(host=bh, clean=False)

            assert (repo / "u-boot.bin").exists(), "U-Boot was not built!"

            with contextlib.ExitStack() as cx:
                b = cx.enter_context(tbot.acquire_board(lh))
                ub = cx.enter_context(tbot.acquire_uboot(b))

                safe_flash(ub, repo)
