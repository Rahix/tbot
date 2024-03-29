import typing
import tbot
from tbot.machine import linux

from tbot import tc

Self = typing.TypeVar("Self", bound=linux.LinuxShell)


class SelftestHost(tbot.selectable.LocalLabHost):
    """A host machine for selftests."""

    name = "selftest-local"

    @property
    def workdir(self: Self) -> linux.Path[Self]:
        return linux.Workdir.xdg_runtime(self, "selftest-data")


from . import path, machine, board_machine, testcase  # noqa: F402, E402
from .path import *  # noqa: F403, F401, E402
from .machine import *  # noqa: F403, F401, E402
from .board_machine import *  # noqa: F403, F401, E402
from .tc import *  # noqa: F403, F401, E402
from .testcase import *  # noqa: F403, F401, E402


@tbot.testcase
def selftest_uname(
    lab: typing.Optional[SelftestHost] = None,
) -> None:
    """Test lab-host shell basics."""
    with lab or SelftestHost() as lh:
        lh.exec0("uname", "-a")


@tbot.testcase
def selftest_user(
    lab: typing.Optional[SelftestHost] = None,
) -> None:
    """Test lab-host variable expansion."""
    with lab or SelftestHost() as lh:
        lh.exec0("echo", lh.env("USER"))

        user = lh.env("USER")
        assert "\n" not in user, "Malformed username?"


@tbot.testcase
def selftest_failing(lab: typing.Optional[SelftestHost] = None) -> None:
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
def selftest_skipping(lab: typing.Optional[SelftestHost] = None) -> None:
    """Test skipping a testcase."""

    @tbot.testcase
    def inner() -> typing.Optional[int]:
        tbot.skip("This test is skipped on purpose")
        return 123

    assert inner() is None, "Testcase was not skipped!"


@tbot.testcase  # type: ignore
def selftest(lab: None = None) -> None:
    """Run all selftests."""

    if "really-run-old-selftests" not in tbot.flags:
        tbot.log.warning(
            """\
You just tried invoking the old selftest suite for tbot.  This is deprecated!

Instead, please run tbot's new selftests like this:

    cd /path/to/tbot-sources
    python3 -m pytest selftest/

If you really want to run the old (unsupported) selftest suite,
pass `-f really-run-old-selftests` on the command line. """
        )
        raise NotImplementedError

    with SelftestHost() as lh:
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
            path.selftest_path_files,
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
