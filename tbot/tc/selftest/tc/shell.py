import tbot
import typing
from tbot.machine import linux
from tbot.tc import shell
from tbot.tc.selftest import minisshd

__all__ = ("selftest_tc_shell_copy",)


@tbot.testcase
def selftest_tc_shell_copy(lab: typing.Optional[linux.LabHost] = None,) -> None:
    """Test ``shell.copy``."""
    with lab or tbot.acquire_lab() as lh:
        tbot.log.message("Test copying a file on the same host ...")

        f00 = lh.workdir / ".selftest_file"
        lh.exec0("echo", "Hello World, this is a test!", stdout=f00)
        f01 = lh.workdir / ".selftest_file2"
        if f01.exists():
            lh.exec0("rm", f01)

        shell.copy(f00, f01)
        out = lh.exec0("cat", f01).strip()
        assert out == "Hello World, this is a test!", repr(out)

        if minisshd.check_minisshd(lh):
            tbot.log.message("Test copying a file from an ssh host ...")

            with minisshd.minisshd(lh) as ssh:
                f10 = ssh.workdir / ".selftest-scp-download"
                ssh.exec0("echo", "SSH TEST 1234", stdout=f10)
                f11 = lh.workdir / ".selftest-scp-dwn-target"
                if f11.exists():
                    lh.exec0("rm", f11)

                shell.copy(f10, f11)
                out = lh.exec0("cat", f11).strip()
                assert out == "SSH TEST 1234", repr(out)

                f20 = lh.workdir / ".selftest-scp-upload"
                lh.exec0("echo", "SSH TEST 4321", stdout=f20)
                f21 = ssh.workdir / ".selftest-scp-upl-target"
                if f21.exists():
                    ssh.exec0("rm", f21)

                shell.copy(f20, f21)
                out = ssh.exec0("cat", f21).strip()
                assert out == "SSH TEST 4321", repr(out)
        else:
            tbot.log.message(tbot.log.c("Skip").yellow.bold + " ssh tests.")
