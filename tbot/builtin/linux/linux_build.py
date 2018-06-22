"""
Testcase to build Linux
-----------------------
"""
import typing
import tbot
from tbot import tc


@tbot.testcase
def just_linux_build_clean(tb: tbot.TBot) -> None:
    """
    Build Linux in the currently existing (possibly dirty) Linux tree.

    Cleans all previous build artifacts before building
    """
    linuxdir = tb.call("linux_checkout", clean=False)
    toolchain = tb.call("toolchain_get")
    tb.call("linux_build", builddir=linuxdir, toolchain=toolchain)


@tbot.testcase
def just_linux_build_noclean(tb: tbot.TBot) -> None:
    """
    Build Linux in the currently existing (possibly dirty) Linux tree.

    Does not clean building
    """
    linuxdir = tb.call("linux_checkout", clean=False)
    toolchain = tb.call("toolchain_get")
    image_type = tb.config["linux.image_type", "zImage"]

    @tb.call_then("toolchain_env", toolchain=toolchain)
    def build(tb: tbot.TBot) -> None:  # pylint: disable=unused-variable
        tb.shell.exec0(f"cd {linuxdir}")
        tb.shell.exec0(f"make -j4 {image_type}")


@tbot.testcase
def linux_build(
    tb: tbot.TBot,
    *,
    builddir: tc.LinuxRepository,
    toolchain: tc.Toolchain,
    defconfig: typing.Optional[str] = None,
    image_type: typing.Optional[str] = None,
    do_compile: bool = True,
) -> None:
    """
    Build Linux

    :param builddir: Where to build Linux
    :type builddir: LinuxRepository
    :param toolchain: Which toolchain to use
    :type toolchain: Toolchain
    :param defconfig: What Linux defconfig to use, defaults to ``tb.config["linux.defconfig"]``
    :type defconfig: str
    :param str image_type: What type of image should be build (eg. ``uImage`` or ``zImage``)
    :param do_compile: Whether we should actually run ``make`` or skip it
    :type do_compile: bool
    """
    defconfig = defconfig or tb.config["linux.defconfig"]
    image_type = image_type or tb.config["linux.image_type", "zImage"]

    tbot.log.doc(
        f"""
We are using the `{toolchain.name}` toolchain and will compile \
Linux using the `{defconfig}` defconfig.
"""
    )

    tbot.log.doc("\n### Setting Up The Toolchain ###\n")

    @tb.call_then("toolchain_env", toolchain=toolchain)
    def build(tb: tbot.TBot) -> None:  # pylint: disable=unused-variable
        """ The actual build """
        tbot.log.doc(
            """
### The Build Process ###
Prepare the build process by moving into the build directory and executing the following commands:
"""
        )
        tbot.log.debug(f"Using '{defconfig}'")
        tb.shell.exec0(f"cd {builddir}")
        tb.shell.exec0(f"make mrproper", log_show_stdout=False)
        tb.shell.exec0(f"make {defconfig}", log_show_stdout=False)

        def compile(
            tb: tbot.TBot
        ) -> None:  # pylint: disable=redefined-builtin, unused-variable
            """ The actual compilation process """
            tbot.log.doc("Start the compilation using\n")
            tb.shell.exec0(f"make -j4 {image_type}")

        if do_compile:
            tb.call(compile)
