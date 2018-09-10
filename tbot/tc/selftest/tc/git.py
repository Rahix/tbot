import typing
import tbot
from tbot.machine import linux
from tbot.tc import git

__all__ = ("selftest_tc_git_checkout", "selftest_tc_git_am")

_GIT: typing.Optional[str] = None


@tbot.testcase
def git_prepare(lab: linux.LabHost) -> str:
    global _GIT

    if _GIT is None:
        p = lab.workdir / "selftest-git-remote"

        if p.exists():
            lab.exec0("rm", "-rf", p)

        tbot.log.message("Setting up test repo ...")

        lab.exec0("mkdir", "-p", p)
        lab.exec0("git", "-C", p, "init")
        lab.exec0(
            "echo",
            """\
# TBot Selftest
This repo exists to test TBot's git testcase.

You can safely remove it, but please **do not** modify it as that might
break the tests.""",
            stdout=p / "README.md",
        )
        lab.exec0("git", "-C", p, "add", "README.md")
        lab.exec0(
            "git",
            "-C",
            p,
            "commit",
            "--author",
            "TBot Selftest <none@none>",
            "-m",
            "Initial",
        )

        tbot.log.message("Creating test patch ...")
        lab.exec0(
            "echo",
            """\
# File 2
A second file that will have been added by patching.""",
            stdout=p / "file2.md",
        )

        lab.exec0("git", "-C", p, "add", "file2.md")
        lab.exec0(
            "git",
            "-C",
            p,
            "commit",
            "--author",
            "TBot Selftest <none@none>",
            "-m",
            "Add file2",
        )
        patch_name = lab.exec0("git", "-C", p, "format-patch", "HEAD~1").strip()
        lab.exec0("mv", p / patch_name, lab.workdir / "selftest-git.patch")

        tbot.log.message("Resetting repo ...")
        lab.exec0("git", "-C", p, "reset", "--hard", "HEAD~1")

        _GIT = p._local_str()
        return _GIT
    else:
        return _GIT


@tbot.testcase
def selftest_tc_git_checkout(lab: typing.Optional[linux.LabHost] = None,) -> None:
    with lab or tbot.acquire_lab() as lh:
        remote = git_prepare(lh)
        target = lh.workdir / "selftest-git-checkout"

        if target.exists():
            lh.exec0("rm", "-rf", target)

        repo = git.checkout(remote, target)

        assert (repo / "README.md").is_file()
        assert not (repo / "file2.md").is_file()

        lh.exec0("rm", "-rf", target)


@tbot.testcase
def selftest_tc_git_am(lab: typing.Optional[linux.LabHost] = None,) -> None:
    with lab or tbot.acquire_lab() as lh:
        remote = git_prepare(lh)
        target = lh.workdir / "selftest-git-am"

        if target.exists():
            lh.exec0("rm", "-rf", target)

        repo = git.checkout(remote, target)

        assert (repo / "README.md").is_file()
        assert not (repo / "file2.md").is_file()

        git.am(repo, lh.workdir / "selftest-git.patch")

        assert (repo / "file2.md").is_file()

        lh.exec0(
            "echo",
            """\
# File 2
A second file that will have been added by patching.

## 2.2
This section was added by a second patch""",
            stdout=repo / "file2.md",
        )

        lh.exec0("git", "-C", repo, "add", "file2.md")
        lh.exec0(
            "git",
            "-C",
            repo,
            "commit",
            "--author",
            "TBot Selftest <none@none>",
            "-m",
            "Update file2",
        )

        patch_dir = lh.workdir / "selftest-git-patches"
        lh.exec0("mkdir", "-p", patch_dir)
        lh.exec0("git", "-C", repo, "format-patch", "-o", patch_dir, "HEAD~2")
        lh.exec0("git", "-C", repo, "reset", "--hard", "HEAD~2")

        assert not (repo / "file2.md").is_file()

        git.am(repo, patch_dir)

        assert lh.exec("grep", "2.2", repo / "file2.md")[0] == 0

        lh.exec0("rm", "-rf", target)
        lh.exec0("rm", "-rf", patch_dir)
