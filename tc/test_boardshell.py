"""
Simple testcase to test if the boardshell is working
----------------------------------------------------
"""
import tbot


@tbot.testcase
@tbot.cmdline
def test_boardshell(tb: tbot.TBot) -> None:
    """ Test if the boardshell is working """
    with tb.with_board_uboot() as tbn:
        # tbn.boardshell.exec0("sleep 2")
        assert tbn.boardshell.exec0("echo SOMESTRING") == "SOMESTRING\n"
        if tbn.config["board.shell.is_uboot", True]:
            tbn.boardshell.exec0("coninfo")
            tbn.boardshell.exec0("version")
