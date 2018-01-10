import tbot


@tbot.testcase
def tc_board_corvus(tb):
    tb.log.doc_log("""U-Boot on the Corvus board
============
""")
    tb.call("build_uboot")
    tb.call("install_uboot_to_tftp",
            additional=[(tb.config.get("uboot.env_location"), "env.txt")])
    tb.call("ts_uboot_all")
    tb.call("task_save_artifacts")

    tb.log.doc_log("""
You should now have a working instance of u-boot
""")
