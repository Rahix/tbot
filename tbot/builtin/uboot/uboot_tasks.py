"""
Collection of U-Boot tasks
--------------------------
"""
import tbot

@tbot.testcase
def check_uboot_version(tb: tbot.TBot,
                        uboot_bin: str = "{builddir}/u-boot.bin") -> None:
    """
    Check whether the version of U-Boot running on the board is the same
    as the one supplied as a binary file in uboot_bin.

    :param uboot_bin: Path to the U-Boot binary. "{builddir}" will be replaced
                      with the U-Boot build dir used by tbot.
    :returns: Nothing
    """
    with tb.with_boardshell() as tbn:
        filename = uboot_bin.format(builddir=tb.config["uboot.builddir"])
        strings = tbn.shell.exec0(f"strings {filename} | grep U-Boot", log_show=False)
        version = tbn.boardshell.exec0("version").split('\n')[0]
        tbn.log.log_debug(f"U-Boot Version (on the board) is '{version}'")
        assert version in strings, "U-Boot version does not seem to match"
