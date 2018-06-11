"""
Common TBot tasks
-----------------
"""
import typing
import pathlib
import tbot


@tbot.testcase
def tbot_clean_workdir(tb: tbot.TBot) -> None:
    """
    Clean TBot's workdir, utility testcase to remove
    TBot's files on the labhost
    """
    tb.shell.exec0(f"rm -rvf {tb.shell.workdir}")


@tbot.testcase
def tbot_clean_builddir(tb: tbot.TBot) -> None:
    """
    Clean TBot's workdir, utility testcase to remove
    TBot's files on the labhost
    """
    with tb.machine(tbot.machine.MachineBuild()) as tb:
        tb.shell.exec0(f"rm -rvf {tb.shell.workdir}")


@tbot.testcase
def check_config(tb: tbot.TBot) -> None:
    """ Check validity of configuration """
    warnings = 0

    def warning(msg: str) -> None:
        """ Print a warning message """
        nonlocal warnings
        tbot.log.message(f"\x1B[33;1mWARNING:\x1B[0m {msg}")
        warnings += 1

    def check_exist(key: str, ty: typing.Type, warn: str) -> bool:
        """
        Check if a config key exists
        and has the correct type
        """
        val = tb.config[key, None]
        if val is None:
            warning(f'{warn}, "{key}" must be {ty}')
            return False
        elif not isinstance(val, ty):
            warning(f'"{key}" must be {ty} not {type(val)}')
            return False
        return True

    has_workdir = check_exist(
        "tbot.workdir", pathlib.PurePosixPath, "No workdir specified"
    )
    has_build = check_exist("build.default", str, "No default buildhost specified")
    default_bhcfg = "build." + tb.config["build.default", None]
    if has_build:
        if tb.config[default_bhcfg, None] is None:
            warning("Default buildhost is invalid")
            has_build = False
    has_uboot_builddir = check_exist(
        "uboot.builddir", str, "No U-Boot builddir specified"
    )
    has_tftproot = check_exist(
        "tftp.root", pathlib.PurePosixPath, "No TFTP root directory specified"
    )
    has_tftpdir = check_exist(
        "tftp.directory", pathlib.PurePosixPath, "No TFTP subdirectory specified"
    )

    has_toolchain = check_exist("board.toolchain", str, "No board toolchain specified")
    no_toolchains = False
    has_board_tc = False
    if has_build:
        toolchains = tb.config[default_bhcfg + ".toolchains", dict()]
        if toolchains == dict():
            warning(f"No toolchains available")
            no_toolchains = True
        board_tc = tb.config["board.toolchain", None]
        has_board_tc = check_exist(
            default_bhcfg + ".toolchains." + board_tc,
            typing.Dict,
            "Board toolchain does not exist",
        )

    has_defconfig = check_exist(
        "uboot.defconfig",
        str,
        "No U-Boot defconfig specified, \
you will not be able to\nbuild U-Boot for this board",
    )

    has_power = check_exist(
        "board.power",
        tbot.config.Config,
        "No board power commands specified, you will not be able to\nuse this board",
    )

    has_connect = check_exist(
        "board.serial.command",
        str,
        "No board connect command specified, you will not be able to\nconnect to this board",
    )
    check_exist(
        "board.serial.name",
        str,
        "No serial name specified, this is not \
necessary but recommended\nfor easier log readability",
    )

    has_ub_tests = check_exist("uboot.test", tbot.config.Config, "No test config found")
    has_linux = check_exist(
        "linux.boot_command",
        str,
        "No linux boot command specified, you will not be able to\nboot linux on this board",
    )

    tbot.log.message(f"Config checked, {warnings} warnings")
    tbot.log.message(
        f"""\x1B[1mSummary:\x1B[0m
Workdir........: {'Y' if has_workdir else 'N - Building U-Boot will be impossible'}

U-Boot Build...: {'Y' if has_uboot_builddir and has_board_tc and has_build and not no_toolchains
and has_toolchain and has_defconfig else 'N - Building U-Boot will be impossible'}
U-Boot Connect.: {'Y' if has_power and has_connect else 'N - Connecting to U-Boot will be impossible'}
U-Boot Tests...: {'Y' if has_uboot_builddir and has_ub_tests else 'N - Running U-Boot tests will be impossible'}

TFTP...........: {'Y' if has_tftpdir and has_tftproot else 'N - No TFTP support available'}

Linux Connect..: {'Y' if has_linux and has_power and has_connect else 'N - Connecting to Linux will be impossible'}
"""
    )
