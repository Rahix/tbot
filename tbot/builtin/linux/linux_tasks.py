"""
Collection of Linux tasks
-------------------------
"""
import pathlib
import typing
import tbot
from tbot import tc


@tbot.testcase
def check_linux_version(
    tb: tbot.TBot,
    *,
    vmlinux: pathlib.PurePosixPath,
    buildhost: typing.Optional[str] = None,
) -> None:
    """
    Check whether the version of Linux running on the board is the same
    as the one supplied as a binary file in vmlinux (on the buildhost).

    :param pathlib.PurePosixPath vmlinux: Path to the U-Boot binary
    :param str buildhost: Optional, which buildhost to use
    """
    with tb.with_board_linux() as tb:
        version_board = tb.boardshell.exec0("cat /proc/version").strip()
        tbot.log.debug(f"Linux Version (on the board):\n{version_board}")
    with tb.machine(tbot.machine.MachineBuild(name=buildhost)) as tb:
        version_build = tb.shell.exec0(
            f"strings {vmlinux} | /usr/bin/grep -E '^Linux version'", log_show=False
        ).strip()
    assert version_board == version_build


@tbot.testcase
def linux_checkout(
    tb: tbot.TBot,
    *,
    clean: bool = True,
    buildhost: typing.Optional[str] = None,
    builddir: typing.Optional[pathlib.PurePosixPath] = None,
    patchdir: typing.Optional[pathlib.PurePosixPath] = None,
    repo: typing.Optional[str] = None,
    rev: typing.Optional[str] = None,
) -> tc.LinuxRepository:
    """
    Create a checkout of Linux **on the buildhost**

    :param bool clean: Whether an existing repository should be cleaned
    :param str buildhost: Which buildhost should U-Boot be built on?
    :param pathlib.PurePosixPath builddir: Where to checkout Linux to,
        defaults to ``wd / tb.config["linux.builddir"]``
    :param patchdir: Optional Linux patches to be applied
        ontop of the tree, defaults to ``tb.config["linux.patchdir"]``, supply a
        nonexistent path to force ignoring the patches
    :type patchdir: pathlib.PurePosixPath
    :param repo: Where to get Linux from, defaults to ``tb.config["linux.repository"]``
    :type repo: str
    :param str rev: Revision from the repo to be checked out, defaults to
                    ``tb.config["linux.revision", None]``
    :returns: The Linux checkout as a meta object for other testcases
    :rtype: LinuxRepository
    """
    with tb.machine(tbot.machine.MachineBuild(name=buildhost)) as tb:
        builddir = builddir or tb.shell.workdir / tb.config["linux.builddir"]
        patchdir = patchdir or tb.config["linux.patchdir", None]
        repo = repo or tb.config["linux.repository"]
        rev = rev or tb.config["linux.revision", None]

        docstr = f"""In this document, we assume the following file locations:

* The build directory is `{builddir}`
* The Linux repository is `{repo}`
"""
        docstr += (
            "  (For you it will most likely be `git://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git`)\n"
            if repo
            != "git://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git"
            else ""
        )
        docstr += (
            f"* Board specific patches can be found in `{patchdir}`\n"
            if patchdir is not None
            else ""
        )

        tbot.log.doc(docstr + "\n")

        git_testcase = "git_clean_checkout" if clean else "git_dirty_checkout"

        gitdir = tb.call(git_testcase, repo=repo, target=builddir, rev=rev)
        if patchdir is not None and clean is True:
            tb.call("git_apply_patches", gitdir=gitdir, patchdir=patchdir)
        return tc.LinuxRepository(gitdir)


@tbot.testcase
def linux_checkout_and_build(
    tb: tbot.TBot,
    *,
    builddir: typing.Optional[pathlib.PurePosixPath] = None,
    patchdir: typing.Optional[pathlib.PurePosixPath] = None,
    repo: typing.Optional[str] = None,
    rev: typing.Optional[str] = None,
    toolchain: typing.Optional[tc.Toolchain] = None,
    defconfig: typing.Optional[str] = None,
    image_type: typing.Optional[str] = None,
) -> tc.LinuxRepository:
    """
    Checkout Linux and build it

    :param builddir: Where to checkout Linux to, defaults to
        ``wd / tb.config["linux.builddir"]``
    :type builddir: pathlib.PurePosixPath
    :param patchdir: Optional patches to be applied
        ontop of the tree, defaults to ``tb.config["linux.patchdir"]``, supply a
        nonexistent path to force building without patches
    :type patchdir: pathlib.PurePosixPath
    :param repo: Where to get Linux from, defaults to ``tb.config["linux.repository"]``
    :type repo: str
    :param str rev: Revision from the repo to be checked out, defaults to
                    ``tb.config["linux.revision", None]``
    :param toolchain: What toolchain to use, defaults to ``tb.config["board.toolchain"]``
    :type toolchain: Toolchain
    :param defconfig: What defconfig to use, defaults to ``tb.config["linux.defconfig"]``
    :type defconfig: str
    :returns: The Linux checkout as a meta object for other testcases
    :rtype: LinuxRepository
    """

    tbot.log.doc(
        """
## Linux Checkout ##
"""
    )

    linuxdir = tb.call(
        "linux_checkout", builddir=builddir, patchdir=patchdir, repo=repo, rev=rev
    )
    assert isinstance(linuxdir, tc.LinuxRepository)

    toolchain = toolchain or tb.call("toolchain_get")

    tbot.log.doc(
        """
## Linux Build ##
"""
    )

    tb.call(
        "linux_build",
        builddir=linuxdir,
        toolchain=toolchain,
        defconfig=defconfig,
        image_type=image_type,
    )

    return linuxdir
