"""
TBot builtin selftests
----------------------
"""
import tbot
from tbot import tc

@tbot.testcase
def selftest_builtin_errors(tb: tbot.TBot) -> None:
    """ Test whether builtin testcases properly error on invalid input """

    tbot.log.debug("Testing toolchain_env with nonexistent toolchain name ...")
    try:
        tb.call("toolchain_get", fail_ok=True, name="a-toolchain-that-will-never-exist")
    except tc.UnknownToolchainException:
        tbot.log.debug("Catched unknown toolchain exception")
    else:
        raise Exception("toolchain_env did not raise an UnknownToolchainException")

@tbot.testcase
def selftest_builtin_tests(tb: tbot.TBot) -> None:
    """ Test a few things to validate the builtin testcases """

    tbot.log.debug("Create a dummy boardshell with custom parameters")
    with tb.machine(tbot.machine.MachineBoardDummy(
        name="dummy-test-custom-machine",
        power_cmd_on="echo ON > /tmp/dummy-machine-test-custom",
        power_cmd_off="rm /tmp/dummy-machine-test-custom")) as tb:
        out = tb.shell.exec0("cat /tmp/dummy-machine-test-custom")
        assert out == "ON\n"

    tbot.log.debug("Create a custom U-Boot shell")
    with tb.machine(tbot.machine.MachineBoardUBoot(
        name="custom",
        boardname="custom-machine",
        power_cmd_on="",
        power_cmd_off="",
        connect_command="\
sh\nPROMPT_COMMAND=\nPS1='U-Boot> ';sleep 0.1;echo 'Autoboot: ';read dummyvar",
        autoboot_prompt=r"Autoboot:\s+",
        prompt="U-Boot> ")) as tb:
        out = tb.boardshell.exec0("echo Hello Custom World")
        assert out == "Hello Custom World\n"
