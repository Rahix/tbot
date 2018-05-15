"""
TBot selftests
--------------
"""
import tbot

@tbot.testcase
def selftest(tb: tbot.TBot) -> None:
    """ TBot self test """
    tb.log.log_msg("Testing shell functionality ...")
    tb.call("selftest_noenv_shell")
    tb.call("selftest_env_shell")
    tb.call("selftest_board_shell")
    tb.call("selftest_powercycle")
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

    tb.log.log_msg("Testing config ...")
    tb.call("selftest_config")
