import tbot


@tbot.testcase
def test_boardshell(tb):
    with tb.new_boardshell() as tbn:
        boot = tbn.boardshell.poweron()
        tbn.boardshell.exec0("sleep 2")
        assert tbn.boardshell.exec0("echo SOMESTRING") == "SOMESTRING\n"
        tbn.boardshell.exec0("coninfo")
        tbn.boardshell.exec0("version")
