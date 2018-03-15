"""
TBot main entry point
"""
import pathlib
import typing
import argparse
import argcomplete

#pylint: disable=invalid-name
def LabCompleter(**_kwargs: typing.Any) -> typing.List[str]:
    """
    Return a list of all currently available labs for shell completion

    :param _kwargs: Compatibility parameter for argcomplete
    :returns: List of lab names
    """
    lst = []
    try:
        for lab in pathlib.Path("config/labs").iterdir():
            if lab.suffix == ".py":
                lst.append(lab.stem)
    finally:
        return lst #pylint: disable=lost-exception

#pylint: disable=invalid-name
def BoardCompleter(**_kwargs: typing.Any) -> typing.List[str]:
    """
    Return a list of all currently available boards for shell completion

    :param _kwargs: Compatibility parameter for argcomplete
    :returns: List of board names
    """
    lst = []
    try:
        for board in pathlib.Path("config/boards").iterdir():
            if board.suffix == ".py":
                lst.append(board.stem)
    finally:
        return lst #pylint: disable=lost-exception

#pylint: disable=invalid-name
def TestcaseCompleter(**_kwargs: typing.Any) -> typing.List[str]:
    """
    Return a list of all currently available testcases for shell completion

    :param _kwargs: Compatibility parameter for argcomplete
    :returns: List of testcase names
    """
    lst = []
    try:
        tbotpath = pathlib.Path(__file__).absolute().parent

        tbot_path = pathlib.PurePosixPath("{tbotpath}")
        #TODO: Fix this ignoring -d args
        default = [tbot_path / "builtin",
                   "tc"]
        tc_paths = [str(path).format(tbotpath=tbotpath) for path in default]
        from tbot import testcase_collector
        _, testcases = testcase_collector.get_testcases(tc_paths)

        for tc in testcases:
            lst.append(tc)
    finally:
        return lst #pylint: disable=lost-exception

#pylint: disable=too-many-locals, too-many-branches
def main() -> None:
    """ Main entry point of tbot """
    parser = argparse.ArgumentParser(
        prog="tbot",
        description="A test tool for embedded linux development",
        )

    parser.add_argument("lab", type=str, help="name of the lab to connect to") \
        .completer = LabCompleter
    parser.add_argument("board", type=str, help="name of the board to test on") \
        .completer = BoardCompleter
    parser.add_argument("testcase", type=str, nargs="*", default=None,
                        help="name of the testcase to run") \
        .completer = TestcaseCompleter

    parser.add_argument("-c", "--confdir", type=str, default="config",
                        help="Specify alternate configuration directory")
    confdir_path = pathlib.PurePosixPath("{confdir}")
    parser.add_argument("--labconfdir", type=str,
                        default=confdir_path / "labs",
                        help="Specify alternate lab config directory")
    parser.add_argument("--boardconfdir", type=str,
                        default=confdir_path / "boards",
                        help="Specify alternate board config directory")

    tbot_path = pathlib.PurePosixPath("{tbotpath}")
    parser.add_argument("-d", "--tcdir", type=str, action="append",
                        default=[tbot_path / "builtin",
                                 "tc",
                                ],
                        help="Add a directory to the testcase search path")
    parser.add_argument("-l", "--logfile", type=str, default=None,
                        help="Json log file name")
    parser.add_argument("-v", "--verbose", action="append_const", const=0,
                        default=[], help="Increase verbosity")
    parser.add_argument("--list-testcases", action="store_true", default=False,
                        help="List all testcases")
    parser.add_argument("--list-labs", action="store_true", default=False,
                        help="List all labs")
    parser.add_argument("--list-boards", action="store_true", default=False,
                        help="List all boards")

    argcomplete.autocomplete(parser)

    args = parser.parse_args()

    from tbot import config_parser
    from tbot import testcase_collector
    from tbot import logger
    import tbot
    import sys
    import traceback

    tbot_config_path = pathlib.Path(args.confdir) / "tbot.py"
    lab_config_path = pathlib.Path(str(args.labconfdir).format(confdir=args.confdir)) \
        / f"{args.lab}.py"

    if args.list_labs:
        for lab in lab_config_path.parent.iterdir():
            if lab.suffix == ".py":
                print(lab.stem)
        return

    board_config_path = pathlib.Path(str(args.boardconfdir).format(confdir=args.confdir)) \
        / f"{args.board}.py"

    if args.list_boards:
        for board in board_config_path.parent.iterdir():
            if board.suffix == ".py":
                print(board.stem)
        return

    if not args.list_testcases:
        config = config_parser.parse_config([lab_config_path,
                                             board_config_path,
                                             tbot_config_path])

    tbotpath = pathlib.Path(__file__).absolute().parent
    tc_paths = [str(path).format(tbotpath=tbotpath) for path in args.tcdir]
    testcases, cmdline_testcases = testcase_collector.get_testcases(tc_paths)

    if args.list_testcases:
        for tc in testcases:
            print(tc)
        return

    verbosity = logger.Verbosity(logger.Verbosity.INFO + len(args.verbose))
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

    log = logger.Logger(verbosity, logfile)

    with tbot.TBot(config, testcases, log) as tb:
        tb.log.log_msg(f"""\
LAB:   {args.lab:10} name="{tb.config["lab.name"]}"
BOARD: {args.board:10} name="{tb.config["board.name"]}"
LOG:   "{logfile}\"""")

        success = False
        try:
            if args.testcase != []:
                for tc in args.testcase:
                    if tc in cmdline_testcases:
                        tb.call(tc)
                    else:
                        raise Exception(\
"Testcase not found or not suitable for commandline use")
            else:
                @tb.call
                def default(tb: tbot.TBot) -> None: #pylint: disable=unused-variable
                    """ Default testcase is building U-Boot """
                    tb.call("uboot_checkout_and_build")
        except Exception: #pylint: disable=broad-except
            tb.log.log_msg(traceback.format_exc(), tbot.logger.Verbosity.ERROR)
        except KeyboardInterrupt:
            tb.log.layer = 0
            print("\r│  ^C")
            tb.log.log_msg("\x1B[31mTest run aborted by user.", tbot.logger.Verbosity.ERROR)
        else:
            success = True
        finally:
            tb.log.log_msg(f"Log written to \"{logfile}\"")
            tb.log.log(logger.TBotFinishedLogEvent(success))
            tb.log.write_logfile()
        sys.exit(0 if success else 1)
