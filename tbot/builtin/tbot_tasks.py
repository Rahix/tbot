"""
Common TBot tasks
-----------------
"""
import tbot

@tbot.testcase
def tbot_clean_workdir(tb: tbot.TBot) -> None:
    """
    Clean TBot's workdir, utility testcase to remove
    TBot's files on the labhost
    """
    workdir = tb.config["tbot.workdir"]

    tb.shell.exec0(f"rm -rvf {workdir}")
