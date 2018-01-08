""" Testcase to build uboot """
import os
import tbot


@tbot.testcase
def build_uboot(tb):
    """ Build a uboot """
    if not tb.shell.shell_type[0] == "sh":
        raise "Need an sh shell"

    build_dir = os.path.join(
        tb.config.workdir,
        f"u-boot-{tb.config.board_name}")
    tb.call("clean_repo_checkout",
            repo=tb.config.get("uboot.repository"),
            target=build_dir)
    patchdir = tb.config.get("uboot.patchdir")
    if patchdir is not None:
        tb.call("apply_git_patches", gitdir=build_dir, patchdir=patchdir)

    toolchain = tb.config.get("board.toolchain")
    defconfig = tb.config.get("board.defconfig")

    @tb.call_then("toolchain_env", toolchain=toolchain)
    def build(tb): #pylint: disable=unused-variable
        """ The actual build """
        tb.shell.exec0(f"cd {build_dir}")
        tb.shell.exec0(f"make mrproper")
        tb.shell.exec0(f"make {defconfig}")

        @tb.call
        def compile(tb): #pylint: disable=redefined-builtin, unused-variable
            """ The actual compilation process """
            tb.shell.exec0(f"make -j4 all")
