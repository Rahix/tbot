"""
TBOT self test
--------------
"""
import tbot
from tbot import tc

@tbot.testcase
@tbot.cmdline
def selftest(tb: tbot.TBot) -> None:
    """ TBot self test """
    tb.log.log_msg("Testing shell functionality ...")
    tb.call("selftest_noenv_shell")
    tb.call("selftest_env_shell")
    tb.call("selftest_board_shell")
    tb.call("selftest_nested_boardshells")

    tb.log.log_msg("Testing testcase functionality ...")
    tb.call("selftest_testcase_calling")
    tb.call("selftest_test_failures")
    tb.call("selftest_wrong_parameter_type")

    tb.log.log_msg("Testing logger ...")
    tb.call("selftest_logger")

    tb.log.log_msg("Testing builtin testcases ...")
    tb.call("selftest_builtin_tests")
    tb.call("selftest_builtin_errors")

def test_shell(shell: tbot.machine.Machine,
               has_printf: bool,
               has_echo_e: bool) -> None:
    """
    Run a couple of tests on a shell

    :param shell: The shell to run commands on
    :param has_printf: Wether the shell supports printf
    :param has_echo_e: Wether the shell supports echo -e
    :returns: Nothing
    :raises AssertionError: If a test failed
    """

    # Test basic IO, does printf without a newline work?
    out = shell.exec0("echo 'Hello World'")
    assert out == "Hello World\n", "%r != 'Hello World\\n'" % out

    if has_printf:
        out = shell.exec0("printf 'Hello World'")
        assert out == "Hello World", "%r != 'Hello World'" % out
        out = shell.exec0("printf 'Hello\\nWorld'")
        assert out == "Hello\nWorld", "%r != 'Hello\\nWorld'" % out

    if has_echo_e:
        # Test '\r' behaviour, we do not want any '\r\n's in out output,
        # unix style line endings only. Also, standalone '\r's should be made
        # into unix line endings for proper output formatting.
        out = shell.exec0("echo -e 'a string with a \\rin the middle and a \\r\\n\
windows line ending'")
        assert out == "a string with a \nin the middle and a \n\
windows line ending\n", "%r does not match" % out

    # Test return codes
    return_code, _ = shell.exec("true")
    assert return_code == 0, f"Shell returned {return_code} instead of 0"

    return_code, _ = shell.exec("false")
    assert return_code == 1, f"Shell returned {return_code} instead of 1"


@tbot.testcase
@tbot.cmdline
def selftest_noenv_shell(tb: tbot.TBot) -> None:
    """ Test noenv shell functionality """
    with tb.machine(tbot.machine.MachineLabNoEnv()) as tbn:
        test_shell(tbn.shell, True, True)

        # Test if environment is actually not shared
        tbn.shell.exec0("FOOBAR='avalue'")
        out = tbn.shell.exec0("echo $FOOBAR")
        assert out == "\n", f"Environment variable was set when it shouldn't: {repr(out)}"

@tbot.testcase
@tbot.cmdline
def selftest_env_shell(tb: tbot.TBot) -> None:
    """ Test env shell functionality """
    with tb.machine(tbot.machine.MachineLabEnv()) as tbn:
        test_shell(tbn.shell, True, True)

        # Test if environment is actually working
        tbn.shell.exec0("FOOBAR='avalue'")
        out = tbn.shell.exec0("echo $FOOBAR")
        assert out == "avalue\n", f"Environment variable was not set correctly: {repr(out)}"

@tbot.testcase
@tbot.cmdline
def selftest_board_shell(tb: tbot.TBot) -> None:
    """ Test board shell functionality """
    with tb.with_board_uboot() as tbn:
        test_shell(tbn.boardshell,
                   tbn.config["board.shell.support_printf", False],
                   tbn.config["board.shell.support_echo_e", False])

@tbot.testcase
@tbot.cmdline
def selftest_nested_boardshells(tb: tbot.TBot) -> None:
    """ Test if tbot handles nested boardshells correctly """
    with tb.with_board_uboot() as tb1:
        out = tb1.boardshell.exec0("echo Hello World")
        assert out == "Hello World\n", "%r != 'Hello World'" % out

        bs1 = tb1.boardshell

        @tb1.call
        def inner(tb: tbot.TBot) -> None: #pylint: disable=unused-variable
            """ Second attempt of starting a boardshell """
            with tb.with_board_uboot() as tb2:
                out = tb2.boardshell.exec0("echo Hello World")
                assert out == "Hello World\n", "%r != 'Hello World'" % out

                bs2 = tb2.boardshell

                assert bs1 is bs2, "%r is not %r" % (bs1, bs2)

@tbot.testcase
@tbot.cmdline
def selftest_logger(tb: tbot.TBot) -> None:
    """ Test logger """
    text = """\
Esse eligendi optio reiciendis. Praesentium possimus et autem.
Ea in odit sit deleniti est nemo. Distinctio aspernatur facere aut culpa.

Sit veniam ducimus nihil. Totam enim consequuntur vel assumenda quisquam.
Voluptates quidem fugit qui laudantium quia perspiciatis voluptatem
expedita. Placeat et possimus iste explicabo asperiores ipsum.

Magnam commodi libero molestiae. A sequi et qui architecto magni quos.
Rerum consequatur tempora quo nostrum qui. Sint aperiam non quia
consectetur numquam.

Facilis dolorem voluptate laudantium vero quis. Voluptatem quia ipsa
quo pariatur iusto odio omnis. Nulla necessitatibus sapiente et
perferendis dolor. Tempore at ipsum eos molestiae nobis error corporis."""

    custom_ev = tbot.logger.CustomLogEvent(["custom", "event"], text,
                                           tbot.logger.Verbosity.INFO,
                                           {"text": text})

    tb.log.log(custom_ev)

@tbot.testcase
@tbot.cmdline
def selftest_testcase_calling(tb: tbot.TBot) -> None:
    """ Test calling testcases """
    def a_testcase(_tb: tbot.TBot, param: str) -> int:
        """ Sample testcase """
        return int(param)

    out = tb.call(a_testcase, param="123")
    assert out == 123, "Testcase did not return 123: %r" % out

@tbot.testcase
@tbot.cmdline
def selftest_test_failures(tb: tbot.TBot) -> None:
    """ Test a failing testcase """
    def a_failing_testcase(_tb: tbot.TBot) -> None:
        """ A testcase that fails """
        raise Exception("failure?")

    did_raise = False
    try:
        tb.call(a_failing_testcase)
    except Exception as e: #pylint: disable=broad-except
        assert e.args[0] == "failure?", "Testcase raised wrong exception"
        did_raise = True
    assert did_raise is True, "Testcase did not raise an exception"

@tbot.testcase
def selftest_standalone_int_param(_tb: tbot.TBot, *, param: int) -> str:
    """ A testcase with an int parameter """
    return str(param)

@tbot.testcase
@tbot.cmdline
def selftest_wrong_parameter_type(tb: tbot.TBot) -> None:
    """ Test whether TBot detects wrong parameter types """

    import enforce

    def testcase_with_int_param(_tb: tbot.TBot, *, param: int) -> str:
        """ A testcase with an int parameter """
        return str(param)

    tb.log.log_debug("Testing with correct parameter type (standalone) ...")
    out = tb.call("selftest_standalone_int_param", param=20)
    assert out == "20", "Testcase returned wrong result"

    failed = False
    try:
        tb.log.log_debug("Testing with wrong parameter type (standalone) ...")
        out2 = tb.call("selftest_standalone_int_param", param="string_param")
    except enforce.exceptions.RuntimeTypeError:
        failed = True

    assert failed is True, "TBot did not detect a wrong parameter type (result: %r)" % (out2,)

    tb.log.log_debug("Testing with correct parameter type (implicit) ...")
    out = tb.call(testcase_with_int_param, param=20)
    assert out == "20", "Testcase returned wrong result"

    failed = False
    try:
        tb.log.log_debug("Testing with wrong parameter type (implicit) ...")
        out2 = tb.call(testcase_with_int_param, param="string_param")
    except enforce.exceptions.RuntimeTypeError:
        failed = True

    assert failed is True, "TBot did not detect a wrong parameter type (result: %r)" % (out2,)

@tbot.testcase
@tbot.cmdline
def selftest_builtin_errors(tb: tbot.TBot) -> None:
    """ Test whether builtin testcases properly error on invalid input """

    tb.log.log_debug("Testing toolchain_env with nonexistent toolchain name ...")
    try:
        tb.call("toolchain_get", name="a-toolchain-that-will-never-exist")
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
        power_cmd_off="rm /tmp/dummy-machine-test-custom")) as tbn:
        out = tbn.shell.exec0("cat /tmp/dummy-machine-test-custom")
        assert out == "ON\n"

    tb.log.log_debug("Create a custom rlogin shell")
    with tb.machine(tbot.machine.MachineBoardRlogin(
        name="custom",
        boardname="custom-machine",
        power_cmd_on="",
        power_cmd_off="",
        connect_command="sh\nPROMPT_COMMAND=\nPS1='U-Boot> ';read",
        prompt="U-Boot> ",
        timeout=0.1)) as tbn:
        out = tbn.boardshell.exec0("echo Hello Custom World")
        assert out == "Hello Custom World\n"
