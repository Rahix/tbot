"""
Demonstration of a git bisect
"""
import tbot

@tbot.testcase
def demo_bisect(tb: tbot.TBot) -> None:
    """ Demonstrate git bisecting """
    repo = tb.config["uboot.builddir"]
    toolchain = tb.config["board.toolchain"]

    def test(tb: tbot.TBot) -> None:
        """ The test whether a commit is good or bad """
        @tb.call_then("toolchain_env", toolchain=toolchain)
        def do_test(tb): #pylint: disable=unused-variable
            """ Build U-Boot as a test """
            tb.shell.exec0(f"cd {repo}")
            tb.shell.exec0(f"make")

    bad = tb.call("git_bisect",
                  gitdir=repo,
                  good="HEAD~10",
                  and_then=test,
                 )

    bad_commit = tb.shell.exec0(f"cd {repo}; git show {bad}")
    tb.log.log_msg(f"BAD COMMIT:\n{bad_commit}")
