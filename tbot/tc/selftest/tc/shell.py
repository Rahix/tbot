import tbot
import typing
from tbot.machine import linux
from tbot.tc import shell

__all__ = ("selftest_tc_shell_copy",)


@tbot.testcase
def selftest_tc_shell_copy(lab: typing.Optional[linux.LabHost] = None,) -> None:
    """Test ``shell.copy``."""
    with lab or tbot.acquire_lab() as lh:
        f = lh.workdir / ".selftest_file"
        f2 = lh.workdir / ".selftest_file2"

        tbot.log.message("Testing copying a file on the same host ...")

        lh.exec0("echo", "Hello World, this is a test!", stdout=f)

        shell.copy(f, f2)

        out = lh.exec0("cat", f2).strip()
        assert out == "Hello World, this is a test!", out
