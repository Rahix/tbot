"""
TBOT self test
--------------
"""
import tbot

def test_shell(shell, has_printf, has_echo_e):
    """
    Run a couple of tests on a shell

    :param shell: The shell to run commands on instanceof(tbot.shell.Shell)
    :param has_printf: Wether the shell supports printf (bool)
    :param has_echo_e: Wether the shell supports echo -e (bool)
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
def selftest(tb):
    """ TBOT self test """

    @tb.call
    def noenv_shell(tb): #pylint: disable=unused-variable
        """ Test noenv shell functionality """
        with tb.machine(tbot.machine.MachineLabNoEnv()) as tbn:
            test_shell(tbn.shell, True, True)

            # Test if environment is actually not shared
            tbn.shell.exec0("FOOBAR='avalue'")
            out = tbn.shell.exec0("echo $FOOBAR")
            assert out == "\n", f"Environment variable was set when it shouldn't: {repr(out)}"

    @tb.call
    def env_shell(tb): #pylint: disable=unused-variable
        """ Test env shell functionality """
        with tb.machine(tbot.machine.MachineLabEnv()) as tbn:
            test_shell(tbn.shell, True, True)

            # Test if environment is actually working
            tbn.shell.exec0("FOOBAR='avalue'")
            out = tbn.shell.exec0("echo $FOOBAR")
            assert out == "avalue\n", f"Environment variable was not set correctly: {repr(out)}"

    @tb.call
    def board_shell(tb): #pylint: disable=unused-variable
        """ Test board shell functionality """
        with tb.with_boardshell() as tbn:
            test_shell(tbn.boardshell,
                       tbn.config.get("board.shell.support_printf", False),
                       tbn.config.get("board.shell.support_echo_e", False))

    @tb.call
    def nested_boardshells(tb): #pylint: disable=unused-variable
        """ Test if tbot handles nested boardshells correctly """
        with tb.with_boardshell() as tb1:
            out = tb1.boardshell.exec0("echo Hello World")
            assert out == "Hello World\n", "%r != 'Hello World'" % out

            bs1 = tb1.boardshell

            @tb1.call
            def inner(tb): #pylint: disable=unused-variable
                with tb.with_boardshell() as tb2:
                    out = tb2.boardshell.exec0("echo Hello World")
                    assert out == "Hello World\n", "%r != 'Hello World'" % out

                    bs2 = tb2.boardshell

                    assert bs1 is bs2, "%r is not %r" % (bs1, bs2)
