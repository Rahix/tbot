""" TBOT self test """
import tbot

@tbot.testcase
def selftest(tb):
    """ TBOT self test """
    assert tb.shell.shell_type[0] == "sh", "Need an sh shell"

    @tb.call
    def noenv_shell(tb): #pylint: disable=unused-variable
        """ Test noenv shell functionality """
        assert tb.shell.exec0("echo 'Hello World'") == "Hello World"
        assert tb.shell.exec0("printf 'Hello World'") == "Hello World"

    # @tb.call
    def env_shell(tb): #pylint: disable=unused-variable
        """ Test env shell functionality """
        with tb.new_shell(tbot.shell.sh_env.ShellShEnv) as tbn:
            assert tbn.shell.exec0("echo 'Hello World'") == "Hello World"
            assert tbn.shell.exec0("printf 'Hello World'") == "Hello World"
