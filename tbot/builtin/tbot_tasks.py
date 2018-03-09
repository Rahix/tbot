"""
Common TBot tasks
-----------------
"""
import typing
import pathlib
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
    warnings = 0

    def warning(msg: str) -> None:
        """ Print a warning message """
        nonlocal warnings
        tb.log.log_msg(f"\x1B[33;1mWARNING:\x1B[0m {msg}")
        warnings += 1

    def check_exist(key: str, ty: typing.Type, warn: str) -> None:
        """
        Check if a config key exists
        and has the correct type
        """
        val = tb.config[key, None]
        if val is None:
            warning(f"{warn}, \"{key}\" must be {ty}")
        elif not isinstance(val, ty):
            warning(f"\"{key}\" must be {ty} not {type(val)}")

    if tb.config["lab.hostname", None] is None:
        raise Exception("No labhost hostname")

    if tb.config["lab.name", None] is None:
        raise Exception("No lab name")
    if tb.config["board.name", None] is None:
        raise Exception("No board name")

    check_exist("tbot.workdir", pathlib.PurePosixPath, "No workdir specified")
    check_exist("uboot.builddir", pathlib.PurePosixPath, "No U-Boot builddir specified")
    check_exist("tftp.directory", pathlib.PurePosixPath, "No TFTP directory specified")

    toolchains = tb.config["toolchains", dict()]
    if toolchains == dict():
        warning(f"\x1B[33;1mWARNING:\x1B[0m No toolchains available")

    check_exist("board.toolchain", str, "No board toolchain specified")
    check_exist("board.power", tbot.config.Config, "No board power commands specified,\
you will not be able to\nuse this board")

    check_exist("board.serial.command", str, "No board connect command specified,\
you will not be able to\nconnect to this board")
    check_exist("board.serial.name", str, "No serial name specified, this is not\
necessary but recommended\nfor easier log readability")

    check_exist("uboot.test", tbot.config.Config, "No test config found")
    check_exist("uboot.shell.boot_command", str, "No linux boot command specified,\
you will not be able to\nboot linux on this board")

    tb.log.log_msg(f"Config checked, {warnings} warnings")
