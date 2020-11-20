# tbot, Embedded Automation Tool
# Copyright (C) 2019  Harald Seiler
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import typing
import tbot
from tbot.machine import linux
from tbot.tc import git, selftest

__all__ = (
    "selftest_tc_git_checkout",
    "selftest_tc_git_am",
    "selftest_tc_git_apply",
    "selftest_tc_git_bisect",
)

_GIT: typing.Optional[str] = None


@tbot.testcase
def git_prepare(lab: linux.Lab) -> str:
    """Prepare a test git repo."""
    global _GIT

    if _GIT is None:
        # Git committer and author information in case the user's git
        # environment is not set up yet
        lab.env("GIT_AUTHOR_NAME", "tbot selftest")
        lab.env("GIT_AUTHOR_EMAIL", "none@example.com")
        lab.env("GIT_COMMITTER_NAME", "tbot selftest")
        lab.env("GIT_COMMITTER_EMAIL", "none@example.com")

        p = lab.workdir / "selftest-git-remote"

        if p.exists():
            lab.exec0("rm", "-rf", p)

        tbot.log.message("Setting up test repo ...")

        lab.exec0("mkdir", "-p", p)
        lab.exec0("git", "-C", p, "init")
        repo = git.GitRepository(p, clean=False)

        lab.exec0(
            "echo",
            """\
# tbot Selftest
This repo exists to test tbot's git testcase.

You can safely remove it, but please **do not** modify it as that might
break the tests.""",
            linux.RedirStdout(repo / "README.md"),
        )

        repo.add(repo / "README.md")
        repo.commit("Initial", author="tbot Selftest <none@none>")

        tbot.log.message("Creating test patch ...")
        lab.exec0(
            "echo",
            """\
# File 2
A second file that will have been added by patching.""",
            linux.RedirStdout(repo / "file2.md"),
        )

        repo.add(repo / "file2.md")
        repo.commit("Add file2", author="tbot Selftest <none@none>")
        patch_name = repo.git0("format-patch", "HEAD~1").strip()
        lab.exec0("mv", repo / patch_name, lab.workdir / "selftest-git.patch")

        tbot.log.message("Resetting repo ...")
        repo.reset("HEAD~1", git.ResetMode.HARD)

        _GIT = p._local_str()
        return _GIT
    else:
        return _GIT


@tbot.testcase
def selftest_tc_git_checkout(
    lab: typing.Optional[selftest.SelftestHost] = None,
) -> None:
    """Test checking out a repository."""
    with lab or selftest.SelftestHost() as lh:
        remote = git_prepare(lh)
        target = lh.workdir / "selftest-git-checkout"

        if target.exists():
            lh.exec0("rm", "-rf", target)

        tbot.log.message("Cloning repo ...")
        repo = git.GitRepository(target, remote)

        assert (repo / "README.md").is_file()
        assert not (repo / "file2.md").is_file()

        tbot.log.message("Make repo dirty ...")
        lh.exec0("echo", "Test 123", linux.RedirStdout(repo / "file.txt"))

        repo = git.GitRepository(target, remote, clean=False)
        assert (repo / "file.txt").is_file()

        repo = git.GitRepository(target, remote, clean=True)
        assert not (repo / "file.txt").is_file()

        tbot.log.message("Add dirty commit ...")
        lh.exec0("echo", "Test 123", linux.RedirStdout(repo / "file.txt"))
        repo.add(repo / "file.txt")
        repo.commit("Add file.txt", author="tbot Selftest <none@none>")

        repo = git.GitRepository(target, remote, clean=False)
        assert (repo / "file.txt").is_file()

        repo = git.GitRepository(target, remote, clean=True)
        assert not (repo / "file.txt").is_file()

        lh.exec0("rm", "-rf", target)


@tbot.testcase
def selftest_tc_git_apply(lab: typing.Optional[selftest.SelftestHost] = None) -> None:
    """Test applying patches."""
    with lab or selftest.SelftestHost() as lh:
        remote = git_prepare(lh)
        target = lh.workdir / "selftest-git-apply"

        if target.exists():
            lh.exec0("rm", "-rf", target)

        tbot.log.message("Cloning repo ...")
        repo = git.GitRepository(target, remote)

        assert (repo / "README.md").is_file()
        assert not (repo / "file2.md").is_file()

        tbot.log.message("Apply patch ...")
        repo.apply(lh.workdir / "selftest-git.patch")

        assert (repo / "file2.md").is_file()

        repo.add(repo / "file2.md")
        repo.commit("Add file2 from patch", author="tbot Selftest <none@none>")

        lh.exec0(
            "echo",
            """\
# File 2
A second file that will have been added by patching.

## 2.2
This section was added by a second patch""",
            linux.RedirStdout(repo / "file2.md"),
        )

        repo.add(repo / "file2.md")
        repo.commit("Update file2", author="tbot Selftest <none@none>")

        patch_dir = lh.workdir / "selftest-git-patches"
        lh.exec0("mkdir", "-p", patch_dir)
        repo.git0("format-patch", "-o", patch_dir, "HEAD~2")
        repo.reset("HEAD~2", git.ResetMode.HARD)

        assert not (repo / "file2.md").is_file()

        tbot.log.message("Apply multiple patches ...")
        repo.apply(patch_dir)

        assert lh.test("grep", "2.2", repo / "file2.md")

        lh.exec0("rm", "-rf", target)
        lh.exec0("rm", "-rf", patch_dir)


@tbot.testcase
def selftest_tc_git_am(lab: typing.Optional[selftest.SelftestHost] = None) -> None:
    """Test applying patches as commits."""
    with lab or selftest.SelftestHost() as lh:
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
            linux.RedirStdout(repo / "file2.md"),
        )

        repo.add(repo / "file2.md")
        repo.commit("Update file2", author="tbot Selftest <none@none>")

        patch_dir = lh.workdir / "selftest-git-patches"
        lh.exec0("mkdir", "-p", patch_dir)
        repo.git0("format-patch", "-o", patch_dir, "HEAD~2")
        repo.reset("HEAD~2", git.ResetMode.HARD)

        assert not (repo / "file2.md").is_file()

        tbot.log.message("Apply multiple patches ...")
        repo.am(patch_dir)

        assert lh.test("grep", "2.2", repo / "file2.md")

        lh.exec0("rm", "-rf", target)
        lh.exec0("rm", "-rf", patch_dir)


@tbot.testcase
def git_increment_commits(repo: git.GitRepository) -> str:
    counter = repo / "counter.txt"

    for i in range(0, 24):
        tbot.log.message(f"Create commit ({i+1:2}/24) ...")

        repo.host.exec0("echo", str(i), linux.RedirStdout(counter))
        repo.add(counter)
        repo.commit(f"Set counter to {i}", author="tbot Selftest <none@none>")

        if i == 0:
            # Take the first commit with counter as good
            rev = repo.head

    return rev


@tbot.testcase
def selftest_tc_git_bisect(lab: typing.Optional[selftest.SelftestHost] = None) -> None:
    """Test the git-bisect testcase."""
    with lab or selftest.SelftestHost() as lh:
        remote = git_prepare(lh)
        target = lh.workdir / "selftest-git-bisect"

        if target.exists():
            lh.exec0("rm", "-rf", target)

        repo = git.GitRepository(target, remote)
        good = git_increment_commits(repo)

        @tbot.testcase
        def check_counter(repo: git.GitRepository) -> bool:
            result = repo.host.exec("cat", repo / "counter.txt")
            return result[0] == 0 and int(result[1].strip()) < 17

        head = repo.symbolic_head

        bad = repo.bisect(good=good, test=check_counter)
        tbot.log.message(f"Bad commit is {bad}!")

        repo.git0("show", bad, linux.Pipe, "cat")

        new_head = repo.symbolic_head
        assert (
            new_head == head
        ), f"Bisect didn't clean up ... ({new_head!r} != {head!r})"
        lh.exec0("rm", "-rf", target)
