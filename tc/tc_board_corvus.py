import tbot


@tbot.testcase
def tc_board_corvus(tb):
    tb.log.doc_log("""U-Boot on the Corvus board
============
""")
    tb.call("build_uboot")
    tb.call("install_uboot_to_tftp",
            additional=[(tb.config.get("uboot.env_location"), "env.txt")])

    tb.log.doc_log("""## Installing UBOOT into NAND flash ##
This is not yet implemented and will be added later (Mostly because I fear it
going wrong ;)
""")

    tb.call("tc_uboot_sandbox")

    tb.log.doc_log("""
You should now have a working instance of u-boot
""")
