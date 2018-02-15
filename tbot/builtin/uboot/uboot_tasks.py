"""
Collection of U-Boot tasks
--------------------------
"""
import pathlib
import tbot

@tbot.testcase
def check_uboot_version(tb: tbot.TBot, *,
                        uboot_binary: pathlib.PurePosixPath,
                       ) -> None:
    """
    Check whether the version of U-Boot running on the board is the same
    as the one supplied as a binary file in uboot_bin.

    :param uboot_binary: Path to the U-Boot binary
    """
    with tb.with_boardshell() as tbn:
        strings = tbn.shell.exec0(f"strings {uboot_binary} | grep U-Boot", log_show=False)
        version = tbn.boardshell.exec0("version").split('\n')[0]
        tbn.log.log_debug(f"U-Boot Version (on the board) is '{version}'")
        assert version in strings, "U-Boot version does not seem to match"
