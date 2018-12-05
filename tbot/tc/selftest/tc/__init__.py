import typing
import tbot
from tbot import tc
from tbot.machine import linux

from .git import *  # noqa: F403
from .shell import *  # noqa: F403
from .build import *  # noqa: F403


@tbot.testcase
def selftest_tc(lab: typing.Optional[linux.LabHost] = None,) -> None:
    """Test builtin testcases."""
    with lab or tbot.acquire_lab() as lh:
        tc.testsuite(
            selftest_tc_git_checkout,  # noqa: F405
            selftest_tc_git_am,  # noqa: F405
            selftest_tc_git_apply,  # noqa: F405
            selftest_tc_git_bisect,  # noqa: F405
            selftest_tc_shell_copy,  # noqa: F405
            selftest_tc_build_toolchain,  # noqa: F405
            lab=lh,
        )
