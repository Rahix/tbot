""" Corvus board specific testcase """
import tbot


@tbot.testcase
@tbot.cmdline
def board_corvus(tb: tbot.TBot) -> None:
    """ Corvus board specific testcase """

    tb.log.doc_log("""U-Boot on the Corvus board
============
""")
    tb.call("uboot_checkout_and_build")

    tb.log.doc_log("""## Installing U-Boot into NAND flash ##
This is not yet implemented and will be added later (Mostly because I fear it
going wrong ;)
""")

    tb.call("uboot_sandbox")
