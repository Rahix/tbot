import tbot


def main() -> None:
    print(tbot.log.c("TBot").yellow.bold + " starting ...")
    from config.labs import dummy as lab
    from config.boards import dummy as board

    tbot.acquire_lab = lambda: lab.LAB()
    tbot.acquire_board = lambda lh: board.BOARD(lh)
    tbot.acquire_uboot = lambda b: board.UBOOT(b)

    import test2

    for n, candy in test2.__dict__.items():
        if hasattr(candy, "_tbot_testcase"):
            tbot.log.message(f"Testcase: {n}")

    tbot.log.EventIO(tbot.log.c("SUCCESS").green.bold, nest_first=tbot.log.u("└─", "\\-"))
