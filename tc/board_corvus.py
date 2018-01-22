""" Corvus board specific testcase """
import tbot


@tbot.testcase
def board_corvus(tb):
    """ Corvus board specific testcase """
    tb.log.doc_log("""U-Boot on the Corvus board
============
""")
    tb.call("build_uboot")

    tb.log.doc_log("""## Installing UBOOT into NAND flash ##
This is not yet implemented and will be added later (Mostly because I fear it
going wrong ;)
""")

    tb.call("tc_uboot_sandbox")

    tb.log.doc_log("""
You should now have a working instance of u-boot
""")
