"""
Testcase to build U-Boot
------------------------
"""
import typing
import pathlib
import tbot


@tbot.testcase
def build_uboot(tb: tbot.TBot, *,
                builddir: typing.Optional[pathlib.PurePosixPath] = None,
                patchdir: typing.Optional[pathlib.PurePosixPath] = None,
                repo: typing.Optional[str] = None,
                toolchain: typing.Optional[str] = None,
                defconfig: typing.Optional[str] = None,
               ) -> None:
    """
    Build U-Boot

    :param builddir: Where to build U-Boot, defaults to ``tb.config["uboot.builddir"]``
    :param patchdir: Optional U-Boot patches to be applied
        ontop of the tree, defaults to ``tb.config["uboot.patchdir"]``, supply a
        nonexistant path to force building without patches
    :param repo: Where to get U-Boot from, defaults to ``tb.config["uboot.repository"]``
    :param toolchain: What toolchain to use, defaults to ``tb.config["board.toolchain"]``
    :param defconfig: What U-Boot defconfig to use, defaults to ``tb.config["board.defconfig"]``
    """

    tb.log.doc_log("""
## Build U-Boot ##
""")

    build_dir = builddir or tb.config["uboot.builddir"]
    patchdir = patchdir or tb.config["uboot.patchdir", None]
    repo = repo or tb.config["uboot.repository"]
    toolchain = toolchain or tb.config["board.toolchain"]
    defconfig = defconfig or tb.config["board.defconfig"]

    docstr = f"""In this document, we assume the following file locations:

* The build directory is `{build_dir}`
* The U-Boot repository is `{repo}`
"""
    docstr += "(For you it will most likely be `git://git.denx.de/u-boot.git`)\n" \
        if repo != "git://git.denx.de/u-boot.git" else ""
    docstr += f"* Board specific patches can be found in `{patchdir}`\n" \
        if patchdir is not None else ""

    tb.log.doc_log(docstr)


    tb.log.doc_log(f"""
We are using the `{toolchain}` toolchain and will compile \
U-Boot using the `{defconfig}` defconfig.
""")

    tb.call("clean_repo_checkout",
            repo=repo,
            target=build_dir)
    if patchdir is not None:
        tb.call("apply_git_patches", gitdir=build_dir, patchdir=patchdir)

    tb.log.doc_log("\n### Setting up the toolchain ###\n")

    @tb.call_then("toolchain_env", toolchain=toolchain)
    def build(tb: tbot.TBot) -> None: #pylint: disable=unused-variable
        """ The actual build """
        tb.log.doc_log("""
### The build process ###
Prepare the buildprocess by moving into the build directory and executing the following commands:
""")
        tb.log.log_debug(f"Using '{defconfig}'")
        tb.shell.exec0(f"cd {build_dir}")
        tb.shell.exec0(f"make mrproper", log_show_stdout=False)
        tb.shell.exec0(f"make {defconfig}", log_show_stdout=False)

        @tb.call
        def compile(tb: tbot.TBot) -> None: #pylint: disable=redefined-builtin, unused-variable
            """ The actual compilation process """
            tb.log.doc_log("Start the compilation using\n")
            tb.shell.exec0(f"make -j4 all")
