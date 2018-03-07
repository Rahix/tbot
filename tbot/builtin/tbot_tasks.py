"""
Common TBot tasks
-----------------
"""
import tbot

@tbot.testcase
@tbot.cmdline
def tbot_clean_workdir(tb: tbot.TBot) -> None:
    """
    Clean TBot's workdir, utility testcase to remove
    TBot's files on the labhost
    """
    workdir = tb.config["tbot.workdir"]

    tb.shell.exec0(f"rm -rvf {workdir}")

@tbot.testcase
@tbot.cmdline
#pylint: disable=pointless-statement
def tbot_check_config(tb: tbot.TBot) -> None:
    """ Check validity of configuration """
    warns = 0

    tb.config["tbot.workdir"]
    tb.config["uboot.builddir"]
    tb.config["tftp.directory"]
    tb.config["lab.hostname"]
    tb.config["lab.name"]
    tb.config["board.name"]

    toolchains = tb.config["toolchains", dict()]
    if toolchains == dict():
        tb.log.log_msg(f"\x1B[33;1mWARNING:\x1B[0m No toolchains available")
        warns += 1

    if tb.config["board.toolchain", None] is None:
        tb.log.log_msg(f"\x1B[33;1mWARNING:\x1B[0m No board toolchain specified")
        warns += 1

    if tb.config["board.power", None] is None:
        tb.log.log_msg(f"\x1B[33;1mWARNING:\x1B[0m No board power commands specified\n\
You will not be able to use this board!")
        warns += 1

    if tb.config["board.shell.command", None] is None:
        tb.log.log_msg(f"\x1B[33;1mWARNING:\x1B[0m No board connect command specified\n\
You will not be able to connect to this board!")
        warns += 1

    if tb.config["uboot.test", None] is None:
        tb.log.log_msg(f"\x1B[33;1mWARNING:\x1B[0m No test config found")
        warns += 1

    tb.log.log_msg(f"Config checked, {warns} warnings")
