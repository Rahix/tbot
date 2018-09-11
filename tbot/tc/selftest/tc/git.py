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
        repo = git.GitRepository(p)

        lab.exec0(
            "echo",
            """\
# TBot Selftest
This repo exists to test TBot's git testcase.

You can safely remove it, but please **do not** modify it as that might
break the tests.""",
            stdout=repo / "README.md",
        )

        repo.add(repo / "README.md")
        repo.commit("Initial", author="TBot Selftest <none@none>")

        tbot.log.message("Creating test patch ...")
        lab.exec0(
            "echo",
            """\
# File 2
A second file that will have been added by patching.""",
            stdout=repo / "file2.md",
        )

        repo.add(repo / "file2.md")
        repo.commit("Add file2", author="TBot Selftest <none@none>")
        patch_name = repo.git0("format-patch", "HEAD~1").strip()
        lab.exec0("mv", repo / patch_name, lab.workdir / "selftest-git.patch")

        tbot.log.message("Resetting repo ...")
        repo.reset("HEAD~1", git.ResetMode.HARD)

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

        tbot.log.message("Cloning repo ...")
        repo = git.GitRepository(target, remote)

        assert (repo / "README.md").is_file()
        assert not (repo / "file2.md").is_file()

        tbot.log.message("Make repo dirty ...")
        lh.exec0("echo", "Test 123", stdout=repo / "file.txt")

        repo = git.GitRepository(target, remote, clean=False)
        assert (repo / "file.txt").is_file()

        repo = git.GitRepository(target, remote, clean=True)
        assert not (repo / "file.txt").is_file()

        tbot.log.message("Add dirty commit ...")
        lh.exec0("echo", "Test 123", stdout=repo / "file.txt")
        repo.add(repo / "file.txt")
        repo.commit("Add file.txt", author="TBot Selftest <none@none>")

        repo = git.GitRepository(target, remote, clean=False)
        assert (repo / "file.txt").is_file()

        repo = git.GitRepository(target, remote, clean=True)
        assert not (repo / "file.txt").is_file()

        lh.exec0("rm", "-rf", target)


@tbot.testcase
def selftest_tc_git_am(lab: typing.Optional[linux.LabHost] = None,) -> None:
    with lab or tbot.acquire_lab() as lh:
        remote = git_prepare(lh)
        target = lh.workdir / "selftest-git-am"

        if target.exists():
            lh.exec0("rm", "-rf", target)

        tbot.log.message("Cloning repo ...")
        repo = git.GitRepository(target, remote)

        assert (repo / "README.md").is_file()
        assert not (repo / "file2.md").is_file()

        tbot.log.message("Apply patch ...")
        repo.am(lh.workdir / "selftest-git.patch")

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

        repo.add(repo / "file2.md")
        repo.commit("Update file2", author="TBot Selftest <none@none>")

        patch_dir = lh.workdir / "selftest-git-patches"
        lh.exec0("mkdir", "-p", patch_dir)
        lh.exec0("git", "-C", repo, "format-patch", "-o", patch_dir, "HEAD~2")
        repo.reset("HEAD~2", git.ResetMode.HARD)

        assert not (repo / "file2.md").is_file()

        tbot.log.message("Apply multiple patches ...")
        repo.am(patch_dir)

        assert lh.exec("grep", "2.2", repo / "file2.md")[0] == 0

        lh.exec0("rm", "-rf", target)
        lh.exec0("rm", "-rf", patch_dir)
