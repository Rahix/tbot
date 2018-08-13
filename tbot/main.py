import argparse
import traceback
import tbot


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="tbot",
        description="Test and development automation tool, tailored for embedded needs",
    )

    parser.add_argument(
        "testcase",
        nargs="*",
        action="append",
        default=[],
        help="Testcase that should be run.",
    )

    parser.add_argument("-b", "--board", help="Use this board instead of the default.")

    parser.add_argument("-l", "--lab", help="Use this lab instead of the default.")

    parser.add_argument(
        "-T",
        action="append",
        default=[],
        help="Add a directory to the testcase search path.",
    )

    parser.add_argument(
        "-t",
        action="append",
        default=[],
        help="Add a file to the testcase search path.",
    )

    flags = [
        (["--list-testcases"], "List all testcases in the current search path."),
        (["--list-labs"], "List all available labs."),
        (["--list-boards"], "List all available boards."),
        (["-s", "--show"], "Show testcase signatures instead of running them."),
        (["-i", "--interactive"], "Prompt before running each command."),
    ]

    for flag_names, flag_help in flags:
        parser.add_argument(
            *flag_names, action="store_true", help=flag_help
        )

    args = parser.parse_args()

    if args.list_labs:
        raise NotImplementedError()

    if args.list_boards:
        raise NotImplementedError()

    if args.list_testcases:
        raise NotImplementedError()

    return

    if args.subcommand == "list-testcases":
        import test2

        for n, f in test2.__dict__.items():
            if hasattr(f, "_tbot_testcase"):
                print(n)
    elif args.subcommand == "run":
        print(tbot.log.c("TBot").yellow.bold + " starting ...")
        from config.labs import dummy as lab
        from config.boards import dummy as board

        # Set the actual selected types, needs to be ignored by mypy
        # beause this is obviously not good python
        tbot.selectable.LabHost = lab.LAB  # type: ignore
        tbot.selectable.Board = board.BOARD  # type: ignore
        tbot.selectable.UBootMachine = board.UBOOT  # type: ignore

        import test2

        tc = test2.__dict__[args.testcase]

        try:
            tc()
        except Exception as e:
            with tbot.log.EventIO(tbot.log.c("Exception").red.bold + ":") as ev:
                ev.prefix = "  "
                ev.write(traceback.format_exc())

            tbot.log.EventIO(
                tbot.log.c("FAILURE").red.bold, nest_first=tbot.log.u("└─", "\\-")
            )
        else:
            tbot.log.EventIO(
                tbot.log.c("SUCCESS").green.bold, nest_first=tbot.log.u("└─", "\\-")
            )
    else:
        parser.error("Invalid subcommand")
