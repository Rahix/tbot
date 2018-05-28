"""
TBot main entry point
"""
import pathlib
import argparse


# pylint: disable=too-many-locals, too-many-branches
def main() -> None:
    """ Main entry point of tbot """
    parser = argparse.ArgumentParser(
        prog="tbot", description="A test tool for embedded linux development"
    )

    parser.add_argument("lab", type=str, help="name of the lab to connect to")
    parser.add_argument("board", type=str, help="name of the board to test on")
    parser.add_argument(
        "testcase",
        type=str,
        nargs="*",
        default=None,
        help='name of the testcase to run (default: "uboot_checkout_and_build")',
    )

    parser.add_argument(
        "-p",
        "--param",
        type=str,
        action="append",
        default=[],
        help="Set a testcase parameter. Argument must be \
of the form <param-name>=<python-expression>. WARNING: Uses eval!",
    )
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        action="append",
        default=[],
        help="Set a config value. Argument must be \
of the form <option-name>=<python-expression>. WARNING: Uses eval!",
    )
    parser.add_argument(
        "--confdir",
        type=str,
        default="config",
        help='Specify alternate configuration directory (default: "config/")',
    )
    confdir_path = pathlib.PurePosixPath("{confdir}")
    parser.add_argument(
        "--labconfdir",
        type=str,
        default=confdir_path / "labs",
        help='Specify alternate lab config directory (default: "config/labs/")',
    )
    parser.add_argument(
        "--boardconfdir",
        type=str,
        default=confdir_path / "boards",
        help='Specify alternate board config directory (default: "config/boards/")',
    )

    tbot_path = pathlib.PurePosixPath("{tbotpath}")
    parser.add_argument(
        "-d",
        "--tcdir",
        type=str,
        action="append",
        default=[tbot_path / "builtin", "tc"],
        help='Add a directory to the testcase search path. The default search path \
contains TBot\'s builtin testcases and, if it exists, a subdirectory in the current working directory \
named "tc"',
    )
    parser.add_argument(
        "-l",
        "--logfile",
        type=str,
        default=None,
        help='Json log file name (default: "log/<lab>-<board>-<run>.json")',
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="append_const",
        const=0,
        default=[],
        help="Increase verbosity",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="append_const",
        const=0,
        default=[],
        help="Decrease verbosity",
    )
    parser.add_argument(
        "--list-testcases",
        action="store_true",
        default=False,
        help="List all testcases",
    )
    parser.add_argument(
        "--list-labs", action="store_true", default=False, help="List all labs"
    )
    parser.add_argument(
        "--list-boards", action="store_true", default=False, help="List all boards"
    )

    args = parser.parse_args()

    from tbot import config_parser
    from tbot import testcase_collector
    import tbot
    import sys
    import traceback

    tbotpath = pathlib.Path(__file__).absolute().parent
    tbot_config_path = tbotpath / "defaults_config.py"
    tbot_custom_config_path_maybe = pathlib.Path(args.confdir) / "tbot.py"
    if pathlib.Path.absolute(tbot_config_path) == pathlib.Path.absolute(
        tbot_custom_config_path_maybe
    ):
        # If its the same, don't apply it twice
        tbot_custom_config_path = None
    else:
        tbot_custom_config_path = tbot_custom_config_path_maybe
    lab_config_path = (
        pathlib.Path(str(args.labconfdir).format(confdir=args.confdir))
        / f"{args.lab}.py"
    )

    if args.list_labs:
        for lab in lab_config_path.parent.iterdir():
            if lab.suffix == ".py":
                print(lab.stem)
        return

    board_config_path = (
        pathlib.Path(str(args.boardconfdir).format(confdir=args.confdir))
        / f"{args.board}.py"
    )

    if args.list_boards:
        for board in board_config_path.parent.iterdir():
            if board.suffix == ".py":
                print(board.stem)
        return

    config = tbot.config.Config()
    if not args.list_testcases:
        # pylint: disable=eval-used
        opts = list(
            map(
                lambda _opt: (_opt[0], eval(_opt[1])),
                (opt.split("=", maxsplit=1) for opt in args.config),
            )
        )
        # Apply before loading config to set values that are used in the config
        for opt_name, opt_val in opts:
            config[opt_name] = opt_val
        config_parser.parse_config(
            config,
            [lab_config_path, board_config_path]
            + (
                [tbot_custom_config_path]
                if tbot_custom_config_path is not None
                and pathlib.Path.exists(tbot_custom_config_path)
                else []
            )
            + [tbot_config_path],
        )
        # Apply after loading config to overwrite values
        for opt_name, opt_val in opts:
            config[opt_name] = opt_val

    tc_paths = [str(path).format(tbotpath=tbotpath) for path in args.tcdir]
    testcases = testcase_collector.get_testcases(tc_paths)

    if args.list_testcases:
        for tc in testcases:
            print(tc)
        return

    verbosity = tbot.log.Verbosity(
        max(0, tbot.log.Verbosity.INFO + len(args.verbose) - len(args.quiet))
    )
    if args.logfile is not None:
        logfile = pathlib.Path(args.logfile)
    else:
        logdir = pathlib.Path("log")
        logdir.mkdir(exist_ok=True)
        glob_pattern = f"{args.lab}-{args.board}-*.json"
        new_num = sum(1 for _ in logdir.glob(glob_pattern)) + 1
        logfile = logdir / f"{args.lab}-{args.board}-{new_num:04}.json"
        # Ensure logfile will not overwrite another one
        while logfile.exists():
            new_num += 1
            logfile = logdir / f"{args.lab}-{args.board}-{new_num:04}.json"

    tbot.log.init_log(logfile, verbosity)

    with tbot.TBot(config, testcases) as tb:
        print(
            f"\
{tbot.log.has_color('33;1')}TBot{tbot.log.has_color('0')} starting ..."
        )
        tbot.log.event(
            ["tbot", "info"],
            msg=f"""\
LAB:   {args.lab:10} name="{tb.config["lab.name"]}"
BOARD: {args.board:10} name="{tb.config["board.name"]}"
LOG:   "{logfile}\"""",
            dct={
                "lab": args.lab,
                "board": args.board,
                "lab-name": tb.config["lab.name"],
                "board-name": tb.config["board.name"],
                "testcases": args.testcase,
            },
        )

        success = False
        try:
            # pylint: disable=eval-used
            params = dict(
                map(
                    lambda _param: (_param[0], eval(_param[1])),
                    (param.split("=", maxsplit=1) for param in args.param),
                )
            )
            if args.testcase != []:
                for tc in args.testcase:
                    if tc in testcases:
                        tb.call(tc, **params)
                    else:
                        raise Exception("Testcase not found")
            else:

                @tb.call
                def default(tb: tbot.TBot) -> None:  # pylint: disable=unused-variable
                    """ Default testcase is building U-Boot """
                    tb.call("uboot_checkout_and_build", **params)

        except Exception:  # pylint: disable=broad-except
            tbot.log.message(traceback.format_exc(), tbot.log.Verbosity.ERROR)
        except KeyboardInterrupt:
            tbot.log.set_layer(0)
            print(tbot.log.has_unicode("\r│  ^C", "\r|  ^C"))
            tbot.log.message(
                "\x1B[31mTest run aborted by user.", tbot.log.Verbosity.ERROR
            )
        else:
            success = True
        finally:
            tbot.log.message(f'Log written to "{logfile}"')
            tbot.log_events.tbot_done(success)
            tbot.log.flush_log()
        sys.exit(0 if success else 1)
