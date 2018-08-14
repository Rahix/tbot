from tbot import log
import pathlib
import argparse
import traceback


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="tbot",
        description="Test and development automation tool, tailored for embedded needs",
    )

    parser.add_argument(
        "testcase",
        nargs="*",
        help="Testcase that should be run.",
    )

    parser.add_argument("-b", "--board", help="Use this board instead of the default.")

    parser.add_argument("-l", "--lab", help="Use this lab instead of the default.")

    parser.add_argument(
        "-T",
        metavar="TC-DIR",
        dest="tcdirs",
        action="append",
        default=[],
        help="Add a directory to the testcase search path.",
    )

    parser.add_argument(
        "-t",
        metavar="TC-FILE",
        dest="tcfiles",
        action="append",
        default=[],
        help="Add a file to the testcase search path.",
    )

    flags = [
        (["--list-testcases"], "List all testcases in the current search path."),
        (["--list-labs"], "List all available labs."),
        (["--list-boards"], "List all available boards."),
        (["--list-files"], "List all testcase files."),
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

    from tbot import loader
    files = loader.get_file_list(
        (pathlib.Path(d).absolute() for d in args.tcdirs),
        (pathlib.Path(f).absolute() for f in args.tcfiles),
    )

    if args.list_files:
        for f in files:
            print(f"{f}")
        return

    testcases = loader.collect_testcases(files)

    if args.list_testcases:
        for tc in testcases:
            print(tc)
        return

    if args.show:
        import textwrap
        import inspect

        for i, name in enumerate(args.testcase):
            if i != 0:
                print(log.c("\n=================================\n").dark)
            func = testcases[name]
            signature = name + str(inspect.signature(func))
            print(log.c(signature).bold.yellow)
            print(log.c(f"----------------").dark)
            print(log.c(textwrap.dedent(func.__doc__ or "No docstring available.").strip()).green)
        return

    if args.interactive:
        log.INTERACTIVE = True

    print(log.c("TBot").yellow.bold + " starting ...")
    lab = loader.load_module(
        pathlib.Path(args.lab).absolute()
        if args.lab
        else pathlib.Path.cwd() / "config" / "labs" / "dummy.py"
    )
    board = loader.load_module(pathlib.Path.cwd() / "config" / "boards" / "dummy.py")

    import tbot
    # Set the actual selected types, needs to be ignored by mypy
    # beause this is obviously not good python
    tbot.selectable.LabHost = lab.LAB  # type: ignore
    tbot.selectable.Board = board.BOARD  # type: ignore
    tbot.selectable.UBootMachine = board.UBOOT  # type: ignore

    try:
        for tc in args.testcase:
            testcases[tc]()
    except Exception as e:
        with log.EventIO(tbot.log.c("Exception").red.bold + ":") as ev:
            ev.prefix = "  "
            ev.write(traceback.format_exc())

        log.EventIO(
            tbot.log.c("FAILURE").red.bold, nest_first=tbot.log.u("└─", "\\-")
        )
    else:
        log.EventIO(
            tbot.log.c("SUCCESS").green.bold, nest_first=tbot.log.u("└─", "\\-")
        )
