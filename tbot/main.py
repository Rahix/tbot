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
    for lab in pathlib.Path("config/labs").iterdir():
        if lab.suffix == ".py":
            lst.append(lab.stem)
    return lst

#pylint: disable=invalid-name
def BoardCompleter(**_kwargs: typing.Any) -> typing.List[str]:
    """
    Return a list of all currently available boards for shell completion

    :param _kwargs: Compatibility parameter for argcomplete
    :returns: List of board names
    """
    lst = []
    for board in pathlib.Path("config/boards").iterdir():
        if board.suffix == ".py":
            lst.append(board.stem)
    return lst

#pylint: disable=invalid-name
def TestcaseCompleter(**_kwargs: typing.Any) -> typing.List[str]:
    """
    Return a list of all currently available testcases for shell completion

    :param _kwargs: Compatibility parameter for argcomplete
    :returns: List of testcase names
    """
    lst = []
    tbotpath = pathlib.Path(__file__).absolute().parent

    tbot_path = pathlib.PurePosixPath("{tbotpath}")
    default = [tbot_path / "builtin",
               tbot_path / "builtin" / "uboot",
               "tc"]
    tc_paths = [str(path).format(tbotpath=tbotpath) for path in default]
    from tbot import testcase_collector
    testcases = testcase_collector.get_testcases(tc_paths)

    for tc in testcases:
        lst.append(tc)
    return lst

#pylint: disable=too-many-locals
def main() -> None:
    """ Main entry point of tbot """
    parser = argparse.ArgumentParser(
        prog="tbot",
        description="A test tool for embedded linux development",
        )

    parser.add_argument("lab", type=str, nargs="?", default="local",
                        help="name of the lab to connect to") \
        .completer = LabCompleter
    parser.add_argument("board", type=str, nargs="?", default="corvus",
                        help="name of the board to test on") \
        .completer = BoardCompleter
    parser.add_argument("testcase", type=str, nargs="?", default=None,
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
                                 tbot_path / "builtin" / "uboot",
                                 "tc",
                                ],
                        help="Add a directory to the testcase search path")
    parser.add_argument("-l", "--logfile", type=str, default="log.json",
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
    testcases = testcase_collector.get_testcases(tc_paths)

    if args.list_testcases:
        for tc in testcases:
            print(tc)
        return

    verbosity = logger.Verbosity(logger.Verbosity.INFO + len(args.verbose))
    log = logger.Logger(verbosity,
                        args.logfile)

    with tbot.TBot(config, testcases, log) as tb:
        tb.log.log_msg(f"""\
LAB:   {args.lab:10} name="{tb.config["lab.name"]}"
BOARD: {args.board:10} name="{tb.config["board.name"]}" """)

        try:
            if args.testcase is not None:
                tb.call(args.testcase)
            else:
                @tb.call
                def default(tb: tbot.TBot) -> None: #pylint: disable=unused-variable
                    """ Default testcase is building U-Boot """
                    tb.call("uboot_checkout_and_build")
        except Exception: #pylint: disable=broad-except
            tb.log.log_msg(traceback.format_exc(), tbot.logger.Verbosity.ERROR)
            tb.log.log(logger.TBotFinishedLogEvent(False))
            tb.log.write_logfile()
            sys.exit(1)
        tb.log.log(logger.TBotFinishedLogEvent(True))
