""" TBOT self test """
import tbot

def test_shell(shell, has_printf, has_echo_e):
    """ Run a couple of tests on a shell """

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
    assert tb.shell.shell_type[0] == "sh", "Need an sh shell"

    @tb.call
    def noenv_shell(tb): #pylint: disable=unused-variable
        """ Test noenv shell functionality """
        with tb.new_shell(tbot.shell.sh_noenv.ShellShNoEnv) as tbn:
            st = tbn.shell.shell_type
            assert st == ('sh', 'noenv'), "%r is not a noenv shell" % st
            test_shell(tbn.shell, True, True)

    @tb.call
    def env_shell(tb): #pylint: disable=unused-variable
        """ Test env shell functionality """
        with tb.new_shell(tbot.shell.sh_env.ShellShEnv) as tbn:
            st = tbn.shell.shell_type
            assert st == ('sh', 'env'), "%r is not an env shell" % st
            test_shell(tbn.shell, True, True)

    @tb.call
    def board_shell(tb): #pylint: disable=unused-variable
        """ Test board shell functionality """
        with tb.new_boardshell() as tbn:
            tbn.boardshell.poweron()

            st = tbn.boardshell.shell_type
            assert st[0] == 'board', "%r is not a board shell" % st
            test_shell(tbn.boardshell,
                       tbn.config.get("board.shell.support_printf", False),
                       tbn.config.get("board.shell.support_echo_e", False))
