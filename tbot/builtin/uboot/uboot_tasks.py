"""
Collection of U-Boot tasks
--------------------------
"""
import pathlib
import typing
import tbot
from tbot import tc

EXPORT = ["UBootRepository"]

class UBootRepository(tc.GitRepository):
    """ A meta object to represent a checked out version of U-Boot """
    pass

@tbot.testcase
def check_uboot_version(tb: tbot.TBot, *,
                        uboot_binary: pathlib.PurePosixPath,
                       ) -> None:
    """
    Check whether the version of U-Boot running on the board is the same
    as the one supplied as a binary file in uboot_bin.

    :param uboot_binary: Path to the U-Boot binary
    """
    with tb.with_boardshell() as tbn:
        strings = tbn.shell.exec0(f"strings {uboot_binary} | grep U-Boot", log_show=False)
        version = tbn.boardshell.exec0("version").split('\n')[0]
        tbn.log.log_debug(f"U-Boot Version (on the board) is '{version}'")
        assert version in strings, "U-Boot version does not seem to match"

@tbot.testcase
@tbot.cmdline
def uboot_checkout(tb: tbot.TBot, *,
                   clean: bool = True,
                   builddir: typing.Optional[pathlib.PurePosixPath] = None,
                   patchdir: typing.Optional[pathlib.PurePosixPath] = None,
                   repo: typing.Optional[str] = None,
                  ) -> UBootRepository:
    """
    Create a checkout of U-Boot

    :param clean: Whether an existing repository should be cleaned
    :param builddir: Where to checkout U-Boot to, defaults to ``tb.config["uboot.builddir"]``
    :param patchdir: Optional U-Boot patches to be applied
        ontop of the tree, defaults to ``tb.config["uboot.patchdir"]``, supply a
        nonexistent path to force ignoring the patches
    :param repo: Where to get U-Boot from, defaults to ``tb.config["uboot.repository"]``
    :returns: The U-Boot checkout as a meta object for other testcases
    """

    builddir = builddir or tb.config["uboot.builddir"]
    patchdir = patchdir or tb.config["uboot.patchdir", None]
    repo = repo or tb.config["uboot.repository"]

    docstr = f"""In this document, we assume the following file locations:

* The build directory is `{builddir}`
* The U-Boot repository is `{repo}`
"""
    docstr += "(For you it will most likely be `git://git.denx.de/u-boot.git`)\n" \
        if repo != "git://git.denx.de/u-boot.git" else ""
    docstr += f"* Board specific patches can be found in `{patchdir}`\n" \
        if patchdir is not None else ""

    tb.log.doc_log(docstr + "\n")

    git_testcase = "git_clean_checkout" if clean else "git_dirty_checkout"

    gitdir = tb.call(git_testcase,
                     repo=repo,
                     target=builddir)
    if patchdir is not None and clean is True:
        tb.call("git_apply_patches", gitdir=gitdir, patchdir=patchdir)
    return UBootRepository(gitdir)

@tbot.testcase
@tbot.cmdline
def uboot_checkout_and_build(tb: tbot.TBot, *,
                             builddir: typing.Optional[pathlib.PurePosixPath] = None,
                             patchdir: typing.Optional[pathlib.PurePosixPath] = None,
                             repo: typing.Optional[str] = None,
                             toolchain: typing.Optional[str] = None,
                             defconfig: typing.Optional[str] = None,
                            ) -> UBootRepository:
    """
    Checkout U-Boot and build it

    :param builddir: Where to checkout U-Boot to, defaults to ``tb.config["uboot.builddir"]``
    :param patchdir: Optional U-Boot patches to be applied
        ontop of the tree, defaults to ``tb.config["uboot.patchdir"]``, supply a
        nonexistent path to force building without patches
    :param repo: Where to get U-Boot from, defaults to ``tb.config["uboot.repository"]``
    :param toolchain: What toolchain to use, defaults to ``tb.config["board.toolchain"]``
    :param defconfig: What U-Boot defconfig to use, defaults to ``tb.config["board.defconfig"]``
    :returns: The U-Boot checkout as a meta object for other testcases
    """

    tb.log.doc_log("""
## U-Boot checkout ##
""")

    ubootdir = tb.call("uboot_checkout",
                       builddir=builddir,
                       patchdir=patchdir,
                       repo=repo)

    toolchain = tb.call("toolchain_get", name=toolchain)

    tb.log.doc_log("""
## U-Boot build ##
""")

    tb.call("uboot_build",
            builddir=ubootdir,
            toolchain=toolchain,
            defconfig=defconfig)

    return ubootdir
