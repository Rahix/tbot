"""
Testcase to build U-Boot
------------------------
"""
import typing
import pathlib
import tbot


@tbot.testcase
def uboot_build(tb: tbot.TBot, *,
                builddir: typing.Optional[pathlib.PurePosixPath] = None,
                toolchain: typing.Optional[str] = None,
                defconfig: typing.Optional[str] = None,
               ) -> None:
    """
    Build U-Boot

    :param builddir: Where to build U-Boot, defaults to ``tb.config["uboot.builddir"]``
    :param toolchain: What toolchain to use, defaults to ``tb.config["board.toolchain"]``
    :param defconfig: What U-Boot defconfig to use, defaults to ``tb.config["board.defconfig"]``
    """

    builddir = builddir or tb.config["uboot.builddir"]
    toolchain = toolchain or tb.config["board.toolchain"]
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
