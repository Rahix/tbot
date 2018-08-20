import typing
import tbot
from tbot.machine import linux

__all__ = ["selftest_machine_reentrant", "selftest_machine_labhost_shell"]


@tbot.testcase
def selftest_machine_reentrant(
    lh: typing.Optional[linux.LabHost] = None,
) -> None:
    with lh or tbot.acquire_lab() as lh:
        with lh as h1:
            assert h1.exec0("echo", "FooBar") == "FooBar\n"

        with lh as h2:
            assert h2.exec0("echo", "FooBar2") == "FooBar2\n"


@tbot.testcase
def selftest_machine_labhost_shell(
    lh: typing.Optional[linux.LabHost] = None,
) -> None:
    with lh or tbot.acquire_lab() as lh:
        selftest_machine_shell(lh)


def selftest_machine_shell(
    m: linux.LinuxMachine,
) -> None:
    tbot.log.message("Testing command output ...")
    out = m.exec0("echo", "Hello World")
    assert out == "Hello World\n"

    out = m.exec0("printf", "Hello World")
    assert out == "Hello World"

    out = m.exec0("printf", "Hello\\nWorld")
    assert out == "Hello\nWorld"

    out = m.exec0("printf", "Hello\nWorld")
    assert out == "Hello\nWorld"

    tbot.log.message("Testing return codes ...")
    r, _ = m.exec("true")
    assert r == 0

    r, _ = m.exec("false")
    assert r == 1
