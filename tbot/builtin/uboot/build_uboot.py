"""
Testcase to build U-Boot
------------------------
"""
import typing
import tbot
from tbot import tc

@tbot.testcase
@tbot.cmdline
def just_uboot_build(tb: tbot.TBot) -> None:
    """
    Build U-Boot in the currently existing (possibly dirty) U-Boot tree.
    """
    uboot_dir = tb.call("uboot_checkout", clean=False)
    toolchain = tb.call("toolchain_get")
    tb.call("uboot_build", builddir=uboot_dir, toolchain=toolchain)

@tbot.testcase
def uboot_build(tb: tbot.TBot, *,
                builddir: tc.UBootRepository,
                toolchain: tc.Toolchain,
                defconfig: typing.Optional[str] = None,
               ) -> None:
    """
    Build U-Boot

    :param builddir: Where to build U-Boot
    :type builddir: UBootRepository
    :param toolchain: Which toolchain to use
    :type toolchain: Toolchain
    :param defconfig: What U-Boot defconfig to use, defaults to ``tb.config["board.defconfig"]``
    :type defconfig: str
    """

    defconfig = defconfig or tb.config["board.defconfig"]

    tb.log.doc_log(f"""
We are using the `{toolchain}` toolchain and will compile \
U-Boot using the `{defconfig}` defconfig.
""")

    tb.log.doc_log("\n### Setting up the toolchain ###\n")

    @tb.call_then("toolchain_env", toolchain=toolchain)
    def build(tb: tbot.TBot) -> None: #pylint: disable=unused-variable
        """ The actual build """
        tb.log.doc_log("""
### The build process ###
Prepare the buildprocess by moving into the build directory and executing the following commands:
""")
        tb.log.log_debug(f"Using '{defconfig}'")
        tb.shell.exec0(f"cd {builddir}")
        tb.shell.exec0(f"make mrproper", log_show_stdout=False)
        tb.shell.exec0(f"make {defconfig}", log_show_stdout=False)

        @tb.call
        def compile(tb: tbot.TBot) -> None: #pylint: disable=redefined-builtin, unused-variable
            """ The actual compilation process """
            tb.log.doc_log("Start the compilation using\n")
            tb.shell.exec0(f"make -j4 all")
