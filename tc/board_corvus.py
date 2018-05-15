""" Corvus board specific testcase """
import tbot


@tbot.testcase
def board_corvus(tb: tbot.TBot) -> None:
    """ Corvus board specific testcase """

    tbot.log.doc("""U-Boot on the Corvus board
============
""")
    tb.call("uboot_checkout_and_build")

    tbot.log.doc("""## Installing U-Boot into NAND flash ##
This is not yet implemented and will be added later (Mostly because I fear it
going wrong ;)
""")

    tb.call("uboot_sandbox")
