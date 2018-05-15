"""
Collection of U-Boot tasks
--------------------------
"""
import pathlib
import typing
import tbot
from tbot import tc

@tbot.testcase
def check_uboot_version(tb: tbot.TBot, *,
                        uboot_binary: pathlib.PurePosixPath,
                       ) -> None:
    """
    Check whether the version of U-Boot running on the board is the same
    as the one supplied as a binary file in uboot_bin.

    :param uboot_binary: Path to the U-Boot binary
    :type uboot_binary: pathlib.PurePosixPath
    """
    with tb.with_board_uboot() as tb:
        strings = tb.shell.exec0(f"strings {uboot_binary} | grep U-Boot", log_show=False)
        version = tb.boardshell.exec0("version").split('\n')[0]
        tb.log.log_debug(f"U-Boot Version (on the board) is '{version}'")
        assert version in strings, "U-Boot version does not seem to match"

@tbot.testcase
def uboot_checkout(tb: tbot.TBot, *,
                   clean: bool = True,
                   builddir: typing.Optional[pathlib.PurePosixPath] = None,
                   patchdir: typing.Optional[pathlib.PurePosixPath] = None,
                   repo: typing.Optional[str] = None,
                  ) -> tc.UBootRepository:
    """
    Create a checkout of U-Boot

    :param clean: Whether an existing repository should be cleaned
    :type clean: bool
    :param builddir: Where to checkout U-Boot to, defaults to ``tb.config["uboot.builddir"]``
    :type builddir: pathlib.PurePosixPath
    :param patchdir: Optional U-Boot patches to be applied
        ontop of the tree, defaults to ``tb.config["uboot.patchdir"]``, supply a
        nonexistent path to force ignoring the patches
    :type patchdir: pathlib.PurePosixPath
    :param repo: Where to get U-Boot from, defaults to ``tb.config["uboot.repository"]``
    :type repo: str
    :returns: The U-Boot checkout as a meta object for other testcases
    :rtype: UBootRepository
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
    return tc.UBootRepository(gitdir)

@tbot.testcase
def uboot_checkout_and_build(tb: tbot.TBot, *,
                             builddir: typing.Optional[pathlib.PurePosixPath] = None,
                             patchdir: typing.Optional[pathlib.PurePosixPath] = None,
                             repo: typing.Optional[str] = None,
                             toolchain: typing.Optional[tc.Toolchain] = None,
                             defconfig: typing.Optional[str] = None,
                            ) -> tc.UBootRepository:
    """
    Checkout U-Boot and build it

    :param builddir: Where to checkout U-Boot to, defaults to ``tb.config["uboot.builddir"]``
    :type builddir: pathlib.PurePosixPath
    :param patchdir: Optional U-Boot patches to be applied
        ontop of the tree, defaults to ``tb.config["uboot.patchdir"]``, supply a
        nonexistent path to force building without patches
    :type patchdir: pathlib.PurePosixPath
    :param repo: Where to get U-Boot from, defaults to ``tb.config["uboot.repository"]``
    :type repo: str
    :param toolchain: What toolchain to use, defaults to ``tb.config["board.toolchain"]``
    :type toolchain: Toolchain
    :param defconfig: What U-Boot defconfig to use, defaults to ``tb.config["uboot.defconfig"]``
    :type defconfig: str
    :returns: The U-Boot checkout as a meta object for other testcases
    :rtype: UBootRepository
    """

    tb.log.doc_log("""
## U-Boot checkout ##
""")

    ubootdir = tb.call("uboot_checkout",
                       builddir=builddir,
                       patchdir=patchdir,
                       repo=repo)
    assert isinstance(ubootdir, tc.UBootRepository)

    toolchain = toolchain or tb.call("toolchain_get")

    tb.log.doc_log("""
## U-Boot build ##
""")

    tb.call("uboot_build",
            builddir=ubootdir,
            toolchain=toolchain,
            defconfig=defconfig)

    return ubootdir


@tbot.testcase
def uboot_checkout_and_prepare(tb: tbot.TBot, *,
                               builddir: typing.Optional[pathlib.PurePosixPath] = None,
                               patchdir: typing.Optional[pathlib.PurePosixPath] = None,
                               repo: typing.Optional[str] = None,
                               toolchain: typing.Optional[tc.Toolchain] = None,
                               defconfig: typing.Optional[str] = None,
                              ) -> tc.UBootRepository:
    """
    Checkout U-Boot and prepare for building it (ie in an interactive session
    using ``interactive_build``)

    :param builddir: Where to checkout U-Boot to, defaults to ``tb.config["uboot.builddir"]``
    :type builddir: pathlib.PurePosixPath
    :param patchdir: Optional U-Boot patches to be applied
        ontop of the tree, defaults to ``tb.config["uboot.patchdir"]``, supply a
        nonexistent path to force building without patches
    :type patchdir: pathlib.PurePosixPath
    :param repo: Where to get U-Boot from, defaults to ``tb.config["uboot.repository"]``
    :type repo: str
    :param toolchain: What toolchain to use, defaults to ``tb.config["board.toolchain"]``
    :type toolchain: Toolchain
    :param defconfig: What U-Boot defconfig to use, defaults to ``tb.config["uboot.defconfig"]``
    :type defconfig: str
    :returns: The U-Boot checkout as a meta object for other testcases
    :rtype: UBootRepository
    """

    tb.log.doc_log("""
## U-Boot checkout ##
""")

    ubootdir = tb.call("uboot_checkout",
                       builddir=builddir,
                       patchdir=patchdir,
                       repo=repo)
    assert isinstance(ubootdir, tc.UBootRepository)

    toolchain = toolchain or tb.call("toolchain_get")

    tb.log.doc_log("""
## U-Boot build ##
""")

    tb.call("uboot_build",
            builddir=ubootdir,
            toolchain=toolchain,
            defconfig=defconfig,
            do_compile=False)

    return ubootdir
