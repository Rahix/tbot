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
from tbot.tc import uboot, git, selftest

__all__ = (
    "selftest_tc_uboot_checkout",
    "selftest_tc_uboot_build",
    "selftest_tc_uboot_patched_bisect",
)


def _uboot_prepare(h: linux.LinuxShell) -> uboot.UBootBuilder:
    remote = h.workdir / "selftest-ub-remote"

    if remote.exists():
        h.exec0("rm", "-rf", remote)

    h.exec0("mkdir", remote)
    h.exec0("git", "-C", remote, "init")
    repo = git.GitRepository(target=remote, clean=False)

    makefile = """\
all:
\t@echo "Making all ..."
\ttest ${CC} = "dummy-none-gcc"
\texit 1

defconfig:
\t@echo "Configuring ..."
\ttouch .config

mrproper:
\t@echo "Cleaning ..."
\trm -f .config
\ttouch .cleaned

.PHONY: all defconfig mrproper
"""

    h.exec0("echo", makefile, linux.RedirStdout(repo / "Makefile"))

    repo.add(repo / "Makefile")
    repo.commit("U-Boot Dummy", author="tbot selftest <tbot@tbot>")

    # Create Patch
    patch = """\
From 1d78601502661ae531b00540bf86e145a317f23f Mon Sep 17 00:00:00 2001
From: tbot Selftest <none@none>
Date: Wed, 30 Jan 2019 13:31:12 +0100
Subject: [PATCH] Fix Makefile

---
 Makefile | 1 -
 1 file changed, 1 deletion(-)

diff --git a/Makefile b/Makefile
index b5319d7..0f01838 100644
--- a/Makefile
+++ b/Makefile
@@ -1,7 +1,6 @@
 all:
 \t@echo "Making all ..."
 \ttest ${CC} = "dummy-none-gcc"
-\texit 1
 \n defconfig:
 \t@echo "Configuring ..."
-- \n2.20.1
"""

    patchfile = h.workdir / "uboot-selftest.patch"
    h.exec0("echo", patch, linux.RedirStdout(patchfile))

    class UBootBuilder(uboot.UBootBuilder):
        name = "tbot-selftest"
        remote = repo._local_str()
        defconfig = "defconfig"
        toolchain = "selftest-toolchain"

        def do_patch(self, repo: git.GitRepository) -> None:
            patch = repo.host.workdir / "uboot-selftest.patch"
            repo.am(patch)

    return UBootBuilder()


@tbot.testcase
def selftest_tc_uboot_checkout(lab: typing.Optional[linux.Lab] = None) -> None:
    with lab or selftest.SelftestHost() as lh:
        builder = _uboot_prepare(lh)

        @tbot.testcase
        def checkout_with_host() -> None:
            repo = builder.checkout(host=lh)

            assert (repo / "Makefile").is_file(), "Makefile not found!"

        checkout_with_host()

        @tbot.testcase
        def checkout_with_path(clean: bool) -> None:
            path = lh.workdir / "selftest-uboot-clone"
            if path.exists():
                lh.exec0("touch", path / "dirty")

            repo = builder.checkout(path=path, clean=clean)

            assert (repo / "Makefile").is_file(), "Makefile not found!"
            assert (not clean) == (repo / "dirty").exists(), "Cleaning failed!"

        tbot.log.message("Calling with cleaning ...")
        checkout_with_path(True)
        tbot.log.message("Calling without cleaning ...")
        checkout_with_path(False)


@tbot.testcase
def selftest_tc_uboot_build(lab: typing.Optional[linux.Lab] = None) -> None:
    from tbot.tc.selftest.tc import build

    with tbot.acquire_local() as lh:
        builder = _uboot_prepare(lh)

        build.LocalDummyBuildhost.prepare(lh)
        setattr(lh, "build", lambda: build.LocalDummyBuildhost())

        @tbot.testcase
        def build_with_lab() -> None:
            builder.build(lab=lh)

        build_with_lab()

        @tbot.testcase
        def build_with_buildhost() -> None:
            with lh.build() as bh:
                builder.build(host=bh)

        build_with_buildhost()

        @tbot.testcase
        def build_with_path() -> None:
            with lh.build() as bh:
                path = bh.workdir / "selftest-uboot-build"
                builder.build(path=path)

        build_with_path()

        @tbot.testcase
        def build_with_repo(clean: bool) -> None:
            with lh.build() as bh:
                path = bh.workdir / "selftest-uboot-testbuild"
                if path.exists():
                    bh.exec0("touch", path / "dirty")
                    bh.exec0("rm", "-f", path / ".cleaned")
                repo = builder.checkout(path=path, clean=clean)

                builder.build(repo=repo, clean=clean)
                assert (not clean) == (repo / "dirty").exists(), "Cleaning failed!"
                assert clean == (repo / ".cleaned").exists(), "Mr Proper failed!"

        build_with_repo(True)
        build_with_repo(False)


@tbot.testcase
def selftest_tc_uboot_patched_bisect(lab: typing.Optional[linux.Lab] = None) -> None:
    from tbot.tc.selftest.tc import build, git as git_tc

    with build.LocalDummyBuildhost() as bh:
        bh.prepare(bh)
        builder = _uboot_prepare(bh)

        repo = builder.checkout(host=bh)
        repo.reset("HEAD~1", git.ResetMode.HARD)

        good = git_tc.git_increment_commits(repo)

        @tbot.testcase
        def check(repo: git.GitRepository) -> bool:
            builder.build(unpatched_repo=repo)
            result = repo.host.exec("cat", repo / "counter.txt")
            return result[0] == 0 and int(result[1].strip()) < 17

        bad = repo.bisect(good=good, test=check)
        tbot.log.message(f"Bad commit is {bad}!")
