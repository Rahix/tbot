"""
P2020RDB-PCA board specific testcases
-------------------------------------
"""
import typing
import pathlib
import tbot


@tbot.testcase
def p2020rdb(tb: tbot.TBot) -> None:
    """
    P2020RDB-PCA board specific testcase to build U-Boot, flash it into
    NAND and run the U-Boot test suite
    """
    tbot.log.doc(
        """\
U-Boot on the P2020RDB-PCA board
================================
"""
    )

    ubootdir = tb.call("uboot_checkout_and_build")

    uboot_binary = tb.call("p2020rdb_install_uboot", builddir=ubootdir)

    with tb.with_board_uboot() as tb:
        tb.call("check_uboot_version", uboot_binary=uboot_binary)

        env = tb.boardshell.exec0("printenv", log_show=False)
        tbot.log.doc_appendix(
            "U-Boot environment",
            f"""```sh
{env}
```""",
        )

    tbot.log.doc(
        f"""\
## Preparation for the U-Boot testsuite
Because U-Boot was built on a separate buildhost previously, we need to checkout
U-Boot again, this time on the labhost.
"""
    )
    buildhost = tb.config["build.local"]
    uboot_dir = tb.call("uboot_checkout", buildhost=buildhost, doc=False)
    toolchain = tb.call("toolchain_get", buildhost=buildhost)

    tb.call("uboot_tests", builddir=uboot_dir, toolchain=toolchain)


@tbot.testcase
def p2020rdb_check_install(tb: tbot.TBot) -> None:
    """ Check if the U-Boot installation was successful """
    ubootdir = tb.call("uboot_checkout", clean=False)
    ubfile = tb.call(
        "retrieve_build_artifact", buildfile=ubootdir / "u-boot-with-spl.bin"
    )
    tb.call("check_uboot_version", uboot_binary=ubfile)


@tbot.testcase
def p2020rdb_install_uboot(
    tb: tbot.TBot, *, builddir: typing.Optional[tbot.tc.UBootRepository] = None
) -> pathlib.PurePosixPath:
    """ Install U-Boot into NAND flash of the P2020RDB-PCA """
    tbot.log.doc(
        """
## Installing U-Boot into NAND flash ##

In this guide, we are going to install U-Boot into NAND flash. Set the `SW3` switch \
to `11101010` to enable NAND boot. A copy of the U-Boot environment used, can be found \
in the appendix of this document.
Copy U-Boot into your tftp directory:
"""
    )

    tftpdir = tb.call("setup_tftpdir")

    # Retrieve U-Boot from buildhost
    builddir = builddir or tb.call("uboot_checkout", clean=False)
    ubfile = tb.call(
        "retrieve_build_artifact", buildfile=builddir / "u-boot-with-spl.bin"
    )
    if not isinstance(ubfile, pathlib.PurePosixPath):
        raise Exception("error in retrieve_build_artifact")
    tb.call("cp_to_tftpdir", source=ubfile, tftpdir=tftpdir)

    tbot.log.doc("Find out the size of the U-Boot binary, as we will need it later:\n")

    filename = tftpdir.path / "u-boot-with-spl.bin"
    size = tb.shell.exec0(f"printf '%x' `stat -c '%s' {filename}`")

    tbot.log.debug(f"U-Boot has size {size}")

    @tb.call
    def install(tb: tbot.TBot) -> None:  # pylint: disable=unused-variable
        """ Actually flash to nand """

        tbot.log.doc("Power on the board and download U-Boot via TFTP:\n")

        with tb.with_board_uboot() as tb:
            filename = tftpdir.subdir / "u-boot-with-spl.bin"
            tb.boardshell.exec0(f"tftp 10000000 {filename}", log_show_stdout=False)

            tbot.log.doc("Write it into flash:\n")

            tbot.log.debug("Writing to NAND ...")
            tb.boardshell.exec0(f"nand device 0", log_show_stdout=False)
            tb.boardshell.exec0(f"nand erase.spread 0 {size}")
            tb.boardshell.exec0(f"nand write 10000000 0 {size}")

            tbot.log.doc("Powercycle the board and check the U-Boot version:\n")

    return ubfile
