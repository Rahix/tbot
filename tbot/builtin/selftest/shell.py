"""
TBot shell selftests
--------------------
"""
import tbot

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
                   tbn.config["uboot.shell.support_printf", False],
                   tbn.config["uboot.shell.support_echo_e", False])

@tbot.testcase
@tbot.cmdline
def selftest_powercycle(tb: tbot.TBot) -> None:
    """ Test powercycling a board """
    with tb.with_board_uboot() as tbn:
        tbn.call("selftest_board_shell")
        tbn.boardshell.powercycle()
        tbn.call("selftest_board_shell")

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
