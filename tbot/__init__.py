""" TBOT """
import argparse
import time
import os
import traceback
import sys
import paramiko
from tbot.boardshell import rlogin
from tbot import config_parser
from tbot import logger
from tbot.shell import sh_noenv
from tbot import testcase_collector

from tbot.testcase_collector import testcase


#pylint: disable=too-many-instance-attributes, too-few-public-methods
class TBot:
    """ Base class of TBOT """
    def __init__(self, config, testcases, log, old_inst=None):
        if old_inst is None:
            self.config = config
            self.testcases = testcases
            self.log = log
            self.old_inst = old_inst
            self.shell = None
            self.layer = 0
        else:
            self.config = old_inst.config
            self.testcases = old_inst.testcases
            self.log = old_inst.log
            self.shell = old_inst.shell
            self.layer = old_inst.layer
        # shellnew is set if a new shell should be created
        self.shellnew = None
        # Wether to open a new boardshell
        self.install_boardshell = False

    def __enter__(self):
        class TBotResource:
            """ Wrapped TBOT Instance for ensuring proper cleanup """
            def __init__(self, wrapper):
                self.config = wrapper.config
                self.testcases = wrapper.testcases
                self.log = wrapper.log
                self.shell = wrapper.shell
                if self.shell is None:
                    self.shell = sh_noenv.ShellShNoEnv(self)
                self.layer = wrapper.layer

                if wrapper.install_boardshell is True:
                    self.boardshell = rlogin.BoardShellRLogin(self)

                if wrapper.shellnew is not None:
                    self.shell = wrapper.shellnew(self)

            def new_shell(self, shell):
                """ Create a new tbot instance with a new shell started """
                new_inst = TBot(None, None, None, old_inst=self)
                new_inst.shellnew = shell
                return new_inst

            def new_boardshell(self):
                """ Create a new tbot instance with a boardshell started """
                new_inst = TBot(None, None, None, old_inst=self)
                new_inst.install_boardshell = True
                return new_inst

            def call_then(self, tc, **kwargs):
                """ Decorator for calling a calling a testcase with a closure
                    as a parameter """
                def _decorator(f):
                    kwargs["and_then"] = f
                    self.call(tc, **kwargs)
                return _decorator

            def call(self, tc, **kwargs):
                """ Call a testcase

                    tc can be either a string or a closure.
                    If it is a string, the testcase with this name will be
                    called. If it is a closure, the closure will be called
                    as an implicit testcase """
                name = tc if isinstance(tc, str) else f"@{tc.__name__}"
                self.log.log(logger.TestcaseBeginLogEvent(name, self.layer))
                self.layer += 1
                start_time = time.monotonic()
                try:
                    if isinstance(tc, str):
                        retval = self.testcases[tc](self, **kwargs)
                    else:
                        retval = tc(self, **kwargs)
                    self.layer -= 1
                    run_duration = time.monotonic() - start_time
                    self.log.log(logger.TestcaseEndLogEvent(name, self.layer, run_duration))
                    return retval
                except Exception: #pylint: disable=broad-except
                    # Cleanup is done by "with" handler __exit__
                    traceback.print_exc()
                    self.log.log(logger.TBotFinishedLogEvent(False))
                    sys.exit(1)

        self.tb = TBotResource(self)
        return self.tb

    def __exit__(self, exc_type, exc_value, trceback):
        if hasattr(self.tb, "boardshell"):
            self.tb.log.log(logger.CustomLogEvent(
                ("boardshell_cleanup"),
                "├─\x1B[1mBOARD CLEANUP\x1B[0m",
                logger.Verbosity.INFO))
            #pylint: disable=protected-access
            self.tb.boardshell._cleanup_boardstate()


def main():
    """ Main entry point of tbot """
    parser = argparse.ArgumentParser(
        prog="tbot",
        description="A test tool for embedded linux development",
        )

    parser.add_argument("lab", type=str, help="name of the lab to connect to")
    parser.add_argument("board", type=str, help="name of the board to test on")
    parser.add_argument("testcase", type=str, nargs="?", default=None,
                        help="name of the testcase to run")

    parser.add_argument("-c", "--confdir", type=str, default="config",
                        help="Specify alternate configuration directory")
    parser.add_argument("--labconfdir", type=str,
                        default=os.path.join("{confdir}", "labs"),
                        help="Specify alternate lab config directory")
    parser.add_argument("--boardconfdir", type=str,
                        default=os.path.join("{confdir}", "boards"),
                        help="Specify alternate board config directory")

    parser.add_argument("-d", "--tcdir", type=str, action="append",
                        default=[os.path.join("{tbotpath}", "builtin"),
                                 os.path.join("{tbotpath}", "builtin",
                                              "uboot"),
                                 "tc",
                                ],
                        help="Add a directory to the testcase search path")
    parser.add_argument("-l", "--logfile", type=str, default="log.json",
                        help="Json log file name")
    parser.add_argument("-v", "--verbose", action="append_const", const=0,
                        default=[], help="Increase verbosity")

    args = parser.parse_args()

    tbot_config_path = os.path.join(args.confdir, "tbot.toml")
    lab_config_path = os.path.join(
        args.labconfdir.format(confdir=args.confdir),
        f"{args.lab}.toml")
    board_config_path = os.path.join(
        args.boardconfdir.format(confdir=args.confdir),
        f"{args.board}.toml")

    config = config_parser.Config([tbot_config_path,
                                   lab_config_path,
                                   board_config_path])

    tbotpath = os.path.dirname(os.path.realpath(__file__))
    tc_paths = [path.format(tbotpath=tbotpath) for path in args.tcdir]
    testcases = testcase_collector.get_testcases(tc_paths)

    log = logger.Logger(logger.Verbosity.INFO + len(args.verbose),
                        args.logfile)

    with TBot(config, testcases, log) as tb:
        # tb.log.log_info(f"LAB: {config.lab_name}")
        # tb.log.log_info(f"BOARD: {config.board_name}")

        if args.testcase is not None:
            tb.call(args.testcase)
        else:
            @tb.call
            def default(tb): #pylint: disable=unused-variable
                """ Default testcase is building uboot """
                tb.call("build_uboot")
        tb.log.log(logger.TBotFinishedLogEvent(True))
