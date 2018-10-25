import sys
import pathlib
import time
import argparse
from tbot import __about__


def main() -> None:  # noqa: C901
    """Tbot main entry point."""
    parser = argparse.ArgumentParser(
        prog=__about__.__title__, description=__about__.__summary__
    )

    parser.add_argument("testcase", nargs="*", help="testcase that should be run.")

    parser.add_argument("-b", "--board", help="use this board instead of the default.")

    parser.add_argument("-l", "--lab", help="use this lab instead of the default.")

    parser.add_argument(
        "-T",
        metavar="TC-DIR",
        dest="tcdirs",
        action="append",
        default=[],
        help="add a directory to the testcase search path.",
    )

    parser.add_argument(
        "-t",
        metavar="TC-FILE",
        dest="tcfiles",
        action="append",
        default=[],
        help="add a file to the testcase search path.",
    )

    parser.add_argument(
        "-f",
        metavar="FLAG",
        dest="flags",
        action="append",
        default=[],
        help="set a user defined flag to change testcase behaviour",
    )

    parser.add_argument(
        "-v", dest="verbosity", action="count", default=0, help="increase the verbosity"
    )

    parser.add_argument(
        "-q", dest="quiet", action="count", default=0, help="decrease the verbosity"
    )

    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__about__.__version__}"
    )

    parser.add_argument(
        "--log", metavar="LOGFILE", help="Alternative location for the json log file"
    )

    flags = [
        (["--list-testcases"], "list all testcases in the current search path."),
        (["--list-labs"], "list all available labs."),
        (["--list-boards"], "list all available boards."),
        (["--list-files"], "list all testcase files."),
        (["--list-flags"], "list all flags defined in lab or board config."),
        (["-s", "--show"], "show testcase signatures instead of running them."),
        (["-i", "--interactive"], "prompt before running each command."),
    ]

    for flag_names, flag_help in flags:
        parser.add_argument(*flag_names, action="store_true", help=flag_help)

    args = parser.parse_args()

    from tbot import log

    # Determine LogFile
    if args.log:
        log.LOGFILE = open(args.log, "w")
    else:
        logdir = pathlib.Path.cwd() / "log"
        logdir.mkdir(exist_ok=True)

        lab_name = "none" if args.lab is None else pathlib.Path(args.lab).stem
        board_name = "none" if args.board is None else pathlib.Path(args.board).stem

        prefix = f"{lab_name}-{board_name}"
        glob_pattern = f"{prefix}-*.json"
        new_num = sum(1 for _ in logdir.glob(glob_pattern)) + 1
        logfile = logdir / f"{prefix}-{new_num:04}.json"
        # Ensure logfile will not overwrite another one
        while logfile.exists():
            new_num += 1
            logfile = logdir / f"{prefix}-{new_num:04}.json"

        log.LOGFILE = open(logfile, "w")

    log.VERBOSITY = log.Verbosity(1 + args.verbosity - args.quiet)

    if args.list_labs:
        raise NotImplementedError()

    if args.list_boards:
        raise NotImplementedError()

    from tbot import loader

    files = loader.get_file_list(
        (pathlib.Path(d).resolve() for d in args.tcdirs),
        (pathlib.Path(f).resolve() for f in args.tcfiles),
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
            signature = f"def {name}{str(inspect.signature(func))}:\n    ..."
            try:
                import pygments
                from pygments.lexers import PythonLexer
                from pygments.formatters import TerminalFormatter

                print(
                    pygments.highlight(
                        signature, PythonLexer(), TerminalFormatter()
                    ).strip()
                )
            except ImportError:
                print(log.c(signature).bold.yellow)
            print(log.c(f"----------------").dark)
            print(
                log.c(
                    textwrap.dedent(func.__doc__ or "No docstring available.").strip()
                ).green
            )
        return

    if args.interactive:
        log.INTERACTIVE = True

    print(log.c("TBot").yellow.bold + " starting ...")

    import tbot

    for flag in args.flags:
        tbot.flags.add(flag)

    # Set the actual selected types, needs to be ignored by mypy
    # beause this is obviously not good python
    lab = None
    if args.lab is not None:
        lab = loader.load_module(pathlib.Path(args.lab).resolve())
        tbot.selectable.LabHost = lab.LAB  # type: ignore
    else:
        pass

    board = None
    if args.board is not None:
        board = loader.load_module(pathlib.Path(args.board).resolve())
        tbot.selectable.Board = board.BOARD  # type: ignore
        if hasattr(board, "UBOOT"):
            tbot.selectable.UBootMachine = board.UBOOT  # type: ignore
        if hasattr(board, "LINUX"):
            tbot.selectable.LinuxMachine = board.LINUX  # type: ignore
    else:
        pass

    if args.list_flags:
        import typing

        all_flags: typing.Dict[str, str] = dict()
        if lab is not None and "FLAGS" in lab.__dict__:
            all_flags.update(lab.__dict__["FLAGS"])

        if board is not None and "FLAGS" in board.__dict__:
            all_flags.update(board.__dict__["FLAGS"])

        width = max(map(len, flags))
        for name, description in all_flags.items():
            log.message(log.c(name.ljust(width)).blue + ": " + description)

    try:
        for tc in args.testcase:
            testcases[tc]()
    except Exception as e:  # noqa: E722
        import traceback

        trace = traceback.format_exc()
        with log.EventIO(
            ["exception"],
            log.c("Exception").red.bold + ":",
            verbosity=log.Verbosity.QUIET,
            name=e.__class__.__name__,
            trace=trace,
        ) as ev:
            ev.prefix = "  "
            ev.write(trace)

        duration = time.monotonic() - log.START_TIME
        log.EventIO(
            ["tbot", "end"],
            log.c("FAILURE").red.bold + f" ({duration:.3f}s)",
            nest_first=log.u("└─", "\\-"),
            verbosity=log.Verbosity.QUIET,
            success=False,
            duration=duration,
        )
        sys.exit(1)
    else:
        duration = time.monotonic() - log.START_TIME
        log.EventIO(
            ["tbot", "end"],
            log.c("SUCCESS").green.bold + f" ({duration:.3f}s)",
            nest_first=log.u("└─", "\\-"),
            verbosity=log.Verbosity.QUIET,
            success=True,
            duration=duration,
        )


if __name__ == "__main__":
    main()
