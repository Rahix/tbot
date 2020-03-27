import typing
import tbot
from tbot import tc
from tbot.tc import selftest

from .git import *  # noqa: F403
from .shell import *  # noqa: F403
from .build import *  # noqa: F403
from .uboot import *  # noqa: F403
from .kconfig import *  # noqa: F403


@tbot.testcase
def selftest_tc(lab: typing.Optional[selftest.SelftestHost] = None) -> None:
    """Run selftests for builtin testcases."""
    with lab or selftest.SelftestHost() as lh:
        tc.testsuite(
            selftest_tc_git_checkout,  # noqa: F405
            selftest_tc_git_am,  # noqa: F405
            selftest_tc_git_apply,  # noqa: F405
            selftest_tc_git_bisect,  # noqa: F405
            selftest_tc_shell_copy,  # noqa: F405
            selftest_tc_build_toolchain,  # noqa: F405
            selftest_tc_uboot_checkout,  # noqa: F405
            selftest_tc_uboot_build,  # noqa: F405
            selftest_tc_uboot_patched_bisect,  # noqa: F405
            selftest_tc_kconfig,  # noqa: F405
            lab=lh,
        )
