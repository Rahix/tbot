"""
Simple testcase to test if the boardshell is working
----------------------------------------------------
"""
import tbot


@tbot.testcase
def test_boardshell(tb: tbot.TBot) -> None:
    """ Test if the boardshell is working """
    with tb.with_board_uboot() as tb:
        # tb.boardshell.exec0("sleep 2")
        assert tb.boardshell.exec0("echo SOMESTRING") == "SOMESTRING\n"
        if tb.config["uboot.shell.is_uboot", True]:
            tb.boardshell.exec0("coninfo")
            tb.boardshell.exec0("version")
