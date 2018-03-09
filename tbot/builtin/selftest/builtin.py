"""
TBot builtin selftests
----------------------
"""
import tbot
from tbot import tc

@tbot.testcase
@tbot.cmdline
def selftest_builtin_errors(tb: tbot.TBot) -> None:
    """ Test whether builtin testcases properly error on invalid input """

    tb.log.log_debug("Testing toolchain_env with nonexistent toolchain name ...")
    try:
        tb.call("toolchain_get", fail_ok=True, name="a-toolchain-that-will-never-exist")
    except tc.UnknownToolchainException:
        tb.log.log_debug("Catched unknown toolchain exception")
    else:
        raise Exception("toolchain_env did not raise an UnknownToolchainException")

@tbot.testcase
@tbot.cmdline
def selftest_builtin_tests(tb: tbot.TBot) -> None:
    """ Test a few things to validate the builtin testcases """

    tb.log.log_debug("Create a dummy boardshell with custom parameters")
    with tb.machine(tbot.machine.MachineBoardDummy(
        name="dummy-test-custom-machine",
        power_cmd_on="echo ON > /tmp/dummy-machine-test-custom",
        power_cmd_off="rm /tmp/dummy-machine-test-custom")) as tb:
        out = tb.shell.exec0("cat /tmp/dummy-machine-test-custom")
        assert out == "ON\n"

    tb.log.log_debug("Create a custom U-Boot shell")
    with tb.machine(tbot.machine.MachineBoardUBoot(
        name="custom",
        boardname="custom-machine",
        power_cmd_on="",
        power_cmd_off="",
        connect_command="sh\nPROMPT_COMMAND=\nPS1='U-Boot> ';read",
        prompt="U-Boot> ",
        timeout=0.1)) as tb:
        out = tb.boardshell.exec0("echo Hello Custom World")
        assert out == "Hello Custom World\n"
