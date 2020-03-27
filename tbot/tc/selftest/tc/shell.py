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

import tbot
import typing
from tbot.machine import linux
from tbot.tc import shell, selftest
from tbot.tc.selftest import minisshd

__all__ = ("selftest_tc_shell_copy",)


@tbot.testcase
def selftest_tc_shell_copy(lab: typing.Optional[selftest.SelftestHost] = None) -> None:
    """Test ``shell.copy``."""

    def do_test(a: linux.Path, b: linux.Path, msg: str) -> None:
        if b.exists():
            b.host.exec0("rm", b)
        a.host.exec0("echo", msg, linux.RedirStdout(a))

        shell.copy(a, b)

        out = b.host.exec0("cat", b).strip()
        assert out == msg, repr(out) + " != " + repr(msg)

    with lab or selftest.SelftestHost() as lh:
        tbot.log.message("Test copying a file on the same host ...")
        do_test(
            lh.workdir / ".selftest-copy-local1",
            lh.workdir / ".selftest-copy-local2",
            "Copy locally",
        )

        if minisshd.check_minisshd(lh):
            with minisshd.minisshd(lh) as ssh:
                tbot.log.message("Test downloading a file from an ssh host ...")
                do_test(
                    ssh.workdir / ".selftest-copy-ssh1",
                    lh.workdir / ".selftest-copy-ssh2",
                    "Download via SCP",
                )

                tbot.log.message("Test uploading a file to an ssh host ...")
                do_test(
                    lh.workdir / ".selftest-copy-ssh1",
                    ssh.workdir / ".selftest-copy-ssh2",
                    "Upload via SCP",
                )

                with minisshd.MiniSSHLabHostParamiko(ssh.port) as slp:
                    tbot.log.message(
                        "Test downloading a file from a paramiko ssh host ..."
                    )
                    do_test(
                        slp.workdir / ".selftest-copy-ssh4",
                        lh.workdir / ".selftest-copy-ssh3",
                        "Download via SCP Lab",
                    )

                    tbot.log.message("Test uploading a file to a paramiko ssh host ...")
                    do_test(
                        lh.workdir / ".selftest-copy-ssh3",
                        slp.workdir / ".selftest-copy-ssh4",
                        "Upload via SCP Lab",
                    )

                with minisshd.MiniSSHLabHostSSH(ssh.port) as sls:
                    tbot.log.message(
                        "Test downloading a file from a plain ssh host ..."
                    )
                    do_test(
                        sls.workdir / ".selftest-copy-ssh6",
                        lh.workdir / ".selftest-copy-ssh5",
                        "Download via SCP Lab",
                    )

                    tbot.log.message("Test uploading a file to a plain ssh host ...")
                    do_test(
                        lh.workdir / ".selftest-copy-ssh5",
                        sls.workdir / ".selftest-copy-ssh6",
                        "Upload via SCP Lab",
                    )
        else:
            tbot.log.message(tbot.log.c("Skip").yellow.bold + " ssh tests.")
