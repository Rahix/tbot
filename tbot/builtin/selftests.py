import tbot
from tbot.machine import linux

from tbot.builtin import tbot_builtins


@tbot.testcase
def selftest_uname(lh: linux.LabHost) -> None:
    lh.exec0("uname", "-a")


@tbot.testcase
def selftest_user(lh: linux.LabHost) -> None:
    lh.exec0("echo", linux.Env("USER"))


@tbot.testcase
def selftest() -> None:
    with tbot.acquire_lab() as lh:
        tbot_builtins.testsuite(
            selftest_uname,
            selftest_user,
            lh=lh,
        )
