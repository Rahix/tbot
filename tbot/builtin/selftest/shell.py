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
    assert out == "Hello World\n", f"{out!r} != 'Hello World\\n'"

    if has_printf:
        out = shell.exec0("printf 'Hello World'")
        assert out == "Hello World", f"{out!r} != 'Hello World'"
        out = shell.exec0("printf 'Hello\\nWorld'")
        assert out == "Hello\nWorld", f"{out!r} != 'Hello\\nWorld'"

    if has_echo_e:
        # Test '\r' behaviour, we do not want any '\r\n's in out output,
        # unix style line endings only. Also, standalone '\r's should be made
        # into unix line endings for proper output formatting.

        # Busybox's builtin echo does not support the -e option. To mitigate this,
        # we use the system's echo
        echo = shell.exec0("which echo").strip()
        out = shell.exec0(f"{echo} -e 'a str w \\rand \\r\\n\
win le'")
        assert out == "a str w \nand \n\
win le\n", f"{out!r} does not match"

    # Test long commands
    out = shell.exec0("echo 'A long command that is definitively too long for the\
 standard terminal width but should be able to run ok, nontheless. At least in theory\
 - That is what this test is for ...'")
    assert out == "A long command that is definitively too long for the\
 standard terminal width but should be able to run ok, nontheless. At least in theory\
 - That is what this test is for ...\n", f"{out!r} does not match"

    # Test return codes
    return_code, _ = shell.exec("true")
    assert return_code == 0, f"Shell returned {return_code} instead of 0"

    return_code, _ = shell.exec("false")
    assert return_code == 1, f"Shell returned {return_code} instead of 1"


@tbot.testcase
@tbot.cmdline
def selftest_noenv_shell(tb: tbot.TBot) -> None:
    """ Test noenv shell functionality """
    with tb.machine(tbot.machine.MachineLabNoEnv()) as tb:
        test_shell(tb.shell, True, True)

        # Test if environment is actually not shared
        tb.shell.exec0("FOOBAR='avalue'")
        out = tb.shell.exec0("echo $FOOBAR")
        assert out == "\n", f"Environment variable was set when it shouldn't: {repr(out)}"

@tbot.testcase
@tbot.cmdline
def selftest_env_shell(tb: tbot.TBot) -> None:
    """ Test env shell functionality """
    with tb.machine(tbot.machine.MachineLabEnv()) as tb:
        test_shell(tb.shell, True, True)

        # Test if environment is actually working
        tb.shell.exec0("FOOBAR='avalue'")
        out = tb.shell.exec0("echo $FOOBAR")
        assert out == "avalue\n", f"Environment variable was not set correctly: {repr(out)}"

@tbot.testcase
@tbot.cmdline
def selftest_board_shell(tb: tbot.TBot) -> None:
    """ Test board shell functionality """
    with tb.with_board_uboot() as tb:
        test_shell(tb.boardshell,
                   tb.config["uboot.shell.support_printf", False],
                   tb.config["uboot.shell.support_echo_e", False])
@tbot.testcase
@tbot.cmdline
def selftest_linux_shell(tb: tbot.TBot) -> None:
    """ Test linux shell functionality """
    with tb.with_board_linux() as tb:
        test_shell(tb.boardshell, True, True)

        # Test if environment is actually working
        tb.boardshell.exec0("FOOBAR='avalue'")
        out = tb.boardshell.exec0("echo $FOOBAR")
        assert out == "avalue\n", f"Environment variable was not set correctly: {repr(out)}"

@tbot.testcase
@tbot.cmdline
def selftest_powercycle(tb: tbot.TBot) -> None:
    """ Test powercycling a board """
    with tb.with_board_uboot() as tb:
        tb.call("selftest_board_shell")
        tb.boardshell.powercycle()
        tb.call("selftest_board_shell")

@tbot.testcase
@tbot.cmdline
def selftest_nested_boardshells(tb: tbot.TBot) -> None:
    """ Test if tbot handles nested boardshells correctly """
    with tb.with_board_uboot() as tb1:
        out = tb1.boardshell.exec0("echo Hello World")
        assert out == "Hello World\n", f"{out!r} != 'Hello World'"

        bs1 = tb1.boardshell

        @tb1.call
        def inner(tb: tbot.TBot) -> None: #pylint: disable=unused-variable
            """ Second attempt of starting a boardshell """
            with tb.with_board_uboot() as tb2:
                out = tb2.boardshell.exec0("echo Hello World")
                assert out == "Hello World\n", f"{out!r} != 'Hello World'"

                bs2 = tb2.boardshell

                assert bs1 is bs2, f"{bs1!r} is not {bs2!r}"
