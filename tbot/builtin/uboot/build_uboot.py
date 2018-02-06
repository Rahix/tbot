"""
Testcase to build U-Boot
------------------------
"""
import os
import tbot


@tbot.testcase
def build_uboot(tb: tbot.TBot) -> None:
    """ Build U-Boot for the selected board """

    tb.log.doc_log("""
## Build U-Boot ##
""")

    build_dir = os.path.join(
        tb.config.workdir,
        f"u-boot-{tb.config.board_name}")
    patchdir = tb.config.try_get("uboot.patchdir")

    repo = tb.config.get("uboot.repository")

    docstr = f"""In this document, we assume the following file locations:

* The build directory is `{build_dir}`
* The U-Boot repository is `{repo}`
"""
    docstr += "(For you it will most likely be `git://git.denx.de/u-boot.git`)\n" \
        if repo != "git://git.denx.de/u-boot.git" else ""
    docstr += f"* Board specific patches can be found in `{patchdir}`\n" \
        if patchdir is not None else ""

    tb.log.doc_log(docstr)

    toolchain = tb.config.get("board.toolchain")
    defconfig = tb.config.get("board.defconfig")

    tb.log.doc_log(f"""
We are using the `{toolchain}` toolchain and will compile \
U-Boot using the `{defconfig}` defconfig.
""")

    tb.call("clean_repo_checkout",
            repo=tb.config.get("uboot.repository"),
            target=build_dir)
    if patchdir is not None:
        tb.call("apply_git_patches", gitdir=build_dir, patchdir=patchdir)

    @tb.call_then("toolchain_env", toolchain=toolchain)
    def build(tb: tbot.TBot) -> None: #pylint: disable=unused-variable
        """ The actual build """
        tb.log.doc_log("""
### The build process ###
Prepare the buildprocess by moving into the build directory and executing the following commands:
""")
        tb.shell.exec0(f"cd {build_dir}")
        tb.shell.exec0(f"make mrproper", log_show_stdout=False)
        tb.shell.exec0(f"make {defconfig}", log_show_stdout=False)

        @tb.call
        def compile(tb: tbot.TBot) -> None: #pylint: disable=redefined-builtin, unused-variable
            """ The actual compilation process """
            tb.log.doc_log("Start the compilation using\n")
            tb.shell.exec0(f"make -j4 all")
