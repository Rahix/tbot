import tbot
from tbot.machine import linux


def _kconf_sed(conf: linux.Path, name: str, expr: str) -> None:
    conf.host.exec0(
        "sed", "-i", f"/^\\(# \\)\\?{name}\\(=[ym]\\| is not set\\)$/c{expr}", conf
    )


@tbot.named_testcase("kconfig_set_enabled")
def enable(conf: linux.Path, name: str) -> None:
    """
    Enable a kconfig option.

    Example::

        kconfig.enable(repo / ".config", "CONFIG_AUTO_COMPLETE")

    :param linux.Path conf: Path to kconfig file (usually .config)
    :param str name: Name of the option (with leading ``CONFIG_``)
    """
    tbot.log.message(f"Enabling {name} option ...")
    _kconf_sed(conf, name, f"{name}=y")


@tbot.named_testcase("kconfig_set_module")
def module(conf: linux.Path, name: str) -> None:
    """
    Set a kconfig option to be built as module.

    Example::

        kconfig.module(repo / ".config", "CONFIG_BLK_DEV_NVME")

    :param linux.Path conf: Path to kconfig file (usually .config)
    :param str name: Name of the option (with leading ``CONFIG_``)
    """
    tbot.log.message(f"Setting {name} to be built as a module ...")
    _kconf_sed(conf, name, f"{name}=m")


@tbot.named_testcase("kconfig_set_disabled")
def disable(conf: linux.Path, name: str) -> None:
    """
    Disable a kconfig option.

    Example::

        kconfig.disable(repo / ".config", "CONFIG_AUTO_COMPLETE")

    :param linux.Path conf: Path to kconfig file (usually .config)
    :param str name: Name of the option (with leading ``CONFIG_``)
    """
    tbot.log.message(f"Disabling {name} option ...")
    _kconf_sed(conf, name, f"# {name} is not set")


@tbot.named_testcase("kconfig_set_value")
def set_string_value(conf: linux.Path, name: str, value: str) -> None:
    """
    Set a kconfig string value.

    Example::

        kconfig.set_string_value(repo / ".config", "CONFIG_LOCALVERSION", "-test")

    :param linux.Path conf: Path to kconfig file (usually .config)
    :param str name: Name of the option (with leading ``CONFIG_``)
    :param str value: New string value
    """
    tbot.log.message(f'Setting {name} to "{value}" ...')
    conf.host.exec0(
        "sed",
        "-i",
        f'/^\\(# \\)\\?{name}\\(=".*"\\| is not set\\)$/c{name}="{value}"',
        conf,
    )


@tbot.named_testcase("kconfig_set_value")
def set_hex_value(conf: linux.Path, name: str, value: int) -> None:
    """
    Set a kconfig hex value.

    Example::

        kconfig.set_hex_value(repo / ".config", "CONFIG_SYS_BASE", 0x10000)

    :param linux.Path conf: Path to kconfig file (usually .config)
    :param str name: Name of the option (with leading ``CONFIG_``)
    :param int value: Integer value that should be set (will be converted to hex)
    """
    tbot.log.message(f"Setting {name} to {hex(value)} ...")
    conf.host.exec0(
        "sed",
        "-i",
        f"/^\\(# \\)\\?{name}\\(=\\(0[xX]\\)\\?[0-9a-fA-F]\\+\\| is not set\\)$/c{name}={hex(value)}",
        conf,
    )
