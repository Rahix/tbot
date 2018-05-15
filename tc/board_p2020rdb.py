"""
P2020RDB-PCA board specific testcases
-------------------------------------
"""
import tbot

@tbot.testcase
def p2020rdb(tb: tbot.TBot) -> None:
    """
    P2020RDB-PCA board specific testcase to build U-Boot, flash it into
    NAND and run the U-Boot test suite
    """
    tbot.log.doc("""\
U-Boot on the P2020RDB-PCA board
================================
""")

    ubootdir = tb.call("uboot_checkout_and_build")

    tb.call("p2020rdb_install_uboot")

    with tb.with_board_uboot() as tb:
        tb.call("check_uboot_version", uboot_binary=\
            ubootdir / "u-boot-with-spl.bin")

        env = tb.boardshell.exec0("printenv", log_show=False)
        tbot.log.doc_appendix("U-Boot environment", f"""```sh
{env}
```""")

    toolchain = tb.call("toolchain_get")
    tb.call("uboot_tests", builddir=ubootdir, toolchain=toolchain)

@tbot.testcase
def p2020rdb_check_install(tb: tbot.TBot) -> None:
    """ Check if the U-Boot installation was successful """
    ubootdir = tb.call("uboot_checkout", clean=False)
    tb.call("check_uboot_version", uboot_binary=\
        ubootdir / "u-boot-with-spl.bin")

@tbot.testcase
def p2020rdb_install_uboot(tb: tbot.TBot) -> None:
    """ Install U-Boot into NAND flash of the P2020RDB-PCA """
    tbot.log.doc("""
## Installing U-Boot into NAND flash ##

In this guide, we are going to install U-Boot into NAND flash. Set the `SW3` switch \
to `11101010` to enable NAND boot. A copy of the U-Boot environment used, can be found \
in the appendix of this document.
Copy U-Boot into your tftp directory:
""")

    tftpdir = tb.call("setup_tftpdir")
    tb.call("cp_to_tftpdir", name="u-boot-with-spl.bin", tftpdir=tftpdir)

    tbot.log.doc("Find out the size of the U-Boot binary, as we will need it later:\n")

    filename = tftpdir.path / "u-boot-with-spl.bin"
    size = tb.shell.exec0(f"printf '%x' `stat -c '%s' {filename}`")

    tbot.log.debug(f"U-Boot has size {size}")

    @tb.call
    def install(tb: tbot.TBot) -> None: #pylint: disable=unused-variable
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
