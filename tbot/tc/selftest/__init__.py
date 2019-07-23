import typing
import tbot
from tbot.machine import linux

from tbot import tc

from .path import *  # noqa: F403
from .machine import *  # noqa: F403
from .board_machine import *  # noqa: F403
from .tc import *  # noqa: F403


@tbot.testcase
def selftest_uname(lab: typing.Optional[linux.LabHost] = None,) -> None:
    """Test lab-host shell basics."""
    with lab or tbot.acquire_lab() as lh:
        lh.exec0("uname", "-a")


@tbot.testcase
def selftest_user(lab: typing.Optional[linux.LabHost] = None,) -> None:
    """Test lab-host variable expansion."""
    with lab or tbot.acquire_lab() as lh:
        lh.exec0("echo", lh.env("USER"))


@tbot.testcase
def selftest_failing(lab: typing.Optional[linux.LabHost] = None,) -> None:
    """Test if a testcase failure is properly detected."""

    class CustomException(Exception):
        pass

    @tbot.testcase
    def inner() -> None:
        raise CustomException()

    raised = False
    try:
        inner()
    except CustomException:
        raised = True
    assert raised, "Exception was not raised"


@tbot.testcase
def selftest(lab: typing.Optional[linux.LabHost] = None,) -> None:
    """Run all selftests."""
    with lab or tbot.acquire_lab() as lh:
        tc.testsuite(
            selftest_failing,
            selftest_uname,
            selftest_user,
            selftest_machine_reentrant,  # noqa: F405
            selftest_machine_labhost_shell,  # noqa: F405
            selftest_machine_ssh_shell,  # noqa: F405
            selftest_machine_sshlab_shell,  # noqa: F405
            selftest_path_stat,  # noqa: F405
            selftest_path_integrity,  # noqa: F405
            selftest_board_power,  # noqa: F405
            selftest_board_uboot,  # noqa: F405
            selftest_board_uboot_noab,  # noqa: F405
            selftest_board_linux,  # noqa: F405
            selftest_board_linux_uboot,  # noqa: F405
            selftest_board_linux_standalone,  # noqa: F405
            selftest_board_linux_nopw,  # noqa: F405
            selftest_board_linux_bad_console,  # noqa: F405
            lab=lh,
        )
