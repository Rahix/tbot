import argparse
import tbot


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="tbot",
        description="Test and development automation tool, tailored for embedded needs",
    )

    subparsers = parser.add_subparsers(dest="subcommand")

    subparsers.add_parser(
        "list-testcases",
        help="List all available testcases",
    )

    run_parser = subparsers.add_parser(
        "run",
        help="Run a testcase",
    )

    run_parser.add_argument("testcase")

    args = parser.parse_args()

    if args.subcommand == "list-testcases":
        import test2

        for n, f in test2.__dict__.items():
            if hasattr(f, "_tbot_testcase"):
                print(n)
    elif args.subcommand == "run":
        print(tbot.log.c("TBot").yellow.bold + " starting ...")
        from config.labs import dummy as lab
        from config.boards import dummy as board

        tbot.acquire_lab = lambda: lab.LAB()
        tbot.acquire_board = lambda lh: board.BOARD(lh)
        tbot.acquire_uboot = lambda b: board.UBOOT(b)

        import test2

        tc = test2.__dict__[args.testcase]

        tc()

        tbot.log.EventIO(tbot.log.c("SUCCESS").green.bold, nest_first=tbot.log.u("└─", "\\-"))
    else:
        parser.error("Invalid subcommand")
