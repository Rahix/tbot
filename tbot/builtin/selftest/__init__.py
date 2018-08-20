import typing
import tbot
from tbot.machine import linux

from tbot.builtin import tbot_builtins

from .path import *
from .machine import *


@tbot.testcase
def selftest_uname(
    lh: typing.Optional[linux.LabHost] = None,
) -> None:
    with lh or tbot.acquire_lab() as lh:
        lh.exec0("uname", "-a")


@tbot.testcase
def selftest_user(
    lh: typing.Optional[linux.LabHost] = None,
) -> None:
    with lh or tbot.acquire_lab() as lh:
        lh.exec0("echo", linux.Env("USER"))


@tbot.testcase
def selftest() -> None:
    with tbot.acquire_lab() as lh:
        tbot_builtins.testsuite(
            selftest_machine_reentrant,
            selftest_machine_labhost_shell,
            selftest_path_stat,
            selftest_path_integrity,
            lh=lh,
        )
