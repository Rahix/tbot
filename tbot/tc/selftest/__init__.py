import typing
import tbot
from tbot.machine import linux

from tbot import tc

from . import path, machine, board_machine, testcase
from .path import *  # noqa: F403, F401
from .machine import *  # noqa: F403, F401
from .board_machine import *  # noqa: F403, F401
from .tc import *  # noqa: F403, F401
from .testcase import *  # noqa: F403, F401


@tbot.testcase
def selftest_uname(lab: typing.Optional[linux.Lab] = None,) -> None:
    """Test lab-host shell basics."""
    with lab or tbot.acquire_lab() as lh:
        lh.exec0("uname", "-a")


@tbot.testcase
def selftest_user(lab: typing.Optional[linux.Lab] = None,) -> None:
    """Test lab-host variable expansion."""
    with lab or tbot.acquire_lab() as lh:
        lh.exec0("echo", lh.env("USER"))

        user = lh.env("USER")
        assert "\n" not in user, "Malformed username?"


@tbot.testcase
def selftest_failing(lab: typing.Optional[linux.Lab] = None,) -> None:
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
def selftest_skipping(lab: typing.Optional[linux.Lab] = None,) -> None:
    """Test skipping a testcase."""

    @tbot.testcase
    def inner() -> typing.Optional[int]:
        tbot.skip("This test is skipped on purpose")
        return 123

    assert inner() is None, "Testcase was not skipped!"


@tbot.testcase
def selftest(lab: typing.Optional[linux.Lab] = None,) -> None:
    """Run all selftests."""
    with lab or tbot.acquire_lab() as lh:
        tc.testsuite(
            selftest_failing,
            selftest_skipping,
            selftest_uname,
            selftest_user,
            machine.selftest_machine_reentrant,
            machine.selftest_machine_labhost_shell,
            machine.selftest_machine_ssh_shell,
            machine.selftest_machine_sshlab_shell,
            path.selftest_path_stat,
            path.selftest_path_integrity,
            board_machine.selftest_board_power,
            board_machine.selftest_board_uboot,
            board_machine.selftest_board_uboot_noab,
            board_machine.selftest_board_linux,
            board_machine.selftest_board_linux_uboot,
            board_machine.selftest_board_linux_standalone,
            board_machine.selftest_board_linux_nopw,
            board_machine.selftest_board_linux_bad_console,
            testcase.selftest_with_lab,
            testcase.selftest_with_uboot,
            testcase.selftest_with_linux,
            lab=lh,
        )
