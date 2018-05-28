"""
TBot testcase selftests
-----------------------
"""
import tbot


@tbot.testcase
def selftest_testcase_calling(tb: tbot.TBot) -> None:
    """ Test calling testcases """

    def a_testcase(_tb: tbot.TBot, param: str) -> int:
        """ Sample testcase """
        return int(param)

    out = tb.call(a_testcase, param="123")
    assert out == 123, f"Testcase did not return 123: {out!r}"


@tbot.testcase
def selftest_test_failures(tb: tbot.TBot) -> None:
    """ Test a failing testcase """

    def a_failing_testcase(_tb: tbot.TBot) -> None:
        """ A testcase that fails """
        raise Exception("failure?")

    did_raise = False
    try:
        tb.call(a_failing_testcase, fail_ok=True)
    except Exception as e:  # pylint: disable=broad-except
        assert e.args[0] == "failure?", "Testcase raised wrong exception"
        did_raise = True
    assert did_raise is True, "Testcase did not raise an exception"


@tbot.testcase
def selftest_standalone_int_param(_tb: tbot.TBot, *, param: int) -> str:
    """ A testcase with an int parameter """
    return str(param)


@tbot.testcase
def selftest_wrong_parameter_type(tb: tbot.TBot) -> None:
    """ Test whether TBot detects wrong parameter types """

    import enforce

    def testcase_with_int_param(_tb: tbot.TBot, *, param: int) -> str:
        """ A testcase with an int parameter """
        return str(param)

    tbot.log.debug("Testing with correct parameter type (standalone) ...")
    out = tb.call("selftest_standalone_int_param", param=20)
    assert out == "20", "Testcase returned wrong result"

    failed = False
    try:
        tbot.log.debug("Testing with wrong parameter type (standalone) ...")
        out2 = tb.call(
            "selftest_standalone_int_param", fail_ok=True, param="string_param"
        )
    except enforce.exceptions.RuntimeTypeError:
        failed = True

    assert (
        failed is True
    ), f"TBot did not detect a wrong parameter type (result: {out2!r})"

    tbot.log.debug("Testing with correct parameter type (implicit) ...")
    out = tb.call(testcase_with_int_param, param=20)
    assert out == "20", "Testcase returned wrong result"

    failed = False
    try:
        tbot.log.debug("Testing with wrong parameter type (implicit) ...")
        out2 = tb.call(testcase_with_int_param, fail_ok=True, param="string_param")
    except enforce.exceptions.RuntimeTypeError:
        failed = True

    assert (
        failed is True
    ), f"TBot did not detect a wrong parameter type (result {out2!r})"
