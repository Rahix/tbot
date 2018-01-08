import tbot


@tbot.testcase
def tc_board_corvus(tb):
    tb.call("build_uboot")
    tb.call("install_uboot_to_tftp",
            additional=[(tb.config.get("uboot.env_location"), "env.txt")])
    tb.call("ts_uboot_all")
    tb.call("task_save_artifacts")
