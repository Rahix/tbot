"""
TBot
----
"""
import argparse
import time
import pathlib
import typing
import traceback
import sys
import paramiko
from tbot import config_parser
from tbot import logger
from tbot import testcase_collector
import tbot.machine

from tbot.testcase_collector import testcase

#pylint: disable=too-many-instance-attributes
class TBot:
    """
    Main class of TBOT

    :param config: A configuration to be used
    :param testcase: Testcases available to this instance
    :param log: The logger that TBot should use
    :param new: Whether this is a new instance that should create a noenv machine.
        Always ``True`` unless you know what you are doing.
    :ivar config: :class:`tbot.config_parser.Config()`
    :ivar testcases: All available testcases
    :ivar log: :class:`tbot.logger.Logger()`
    :ivar machines: All available machines :class:`tbot.machine.machine.MachineManager()`
    """
    def __init__(self,
                 config: config_parser.Config,
                 testcases: dict,
                 log: logger.Logger,
                 new: bool = True) -> None:
        self.config = config
        self.testcases = testcases
        self.log = log
        self.layer = 0

        self.destruct_machines: typing.List[tbot.machine.Machine] = list()

        if new:
            self.machines = tbot.machine.MachineManager(self)

            labhost = tbot.machine.MachineLabNoEnv()
            labhost._setup(self) #pylint: disable=protected-access
            self.machines[labhost.common_machine_name] = labhost
            self.machines[labhost.unique_machine_name] = labhost
            self.destruct_machines.append(labhost)

    @property
    def shell(self) -> tbot.machine.Machine:
        """ The default labhost machine """
        return self.machines["labhost"]

    @property
    def boardshell(self) -> tbot.machine.Machine:
        """ The default board machine """
        return self.machines["board"]

    def call_then(self,
                  tc: typing.Union[str, typing.Callable],
                  **kwargs: typing.Any) -> typing.Callable:
        """
        Decorator to call a testcase with a function as a payload ("and_then" argument)

        :param tc: The testcase to call
        :param kwargs: Additional arguments for the testcase
        :returns: The decorated function
        """
        def _decorator(f: typing.Callable) -> typing.Any:
            kwargs["and_then"] = f
            return self.call(tc, **kwargs)
        return _decorator

    def call(self,
             tc: typing.Union[str, typing.Callable],
             **kwargs: typing.Any) -> typing.Any:
        """
        Call a testcase

        :param tc: The testcase to be called. Can either be a string or a callable
        :param kwargs: Additional arguments for the testcase
        :returns: The return value from the testcase
        """
        name = tc if isinstance(tc, str) else f"@{tc.__name__}"
        self.log.log(logger.TestcaseBeginLogEvent(name, self.layer))
        self.layer += 1
        self.log.layer = self.layer
        start_time = time.monotonic()
        try:
            if isinstance(tc, str):
                retval = self.testcases[tc](self, **kwargs)
            else:
                retval = tc(self, **kwargs)
            self.layer -= 1
            self.log.layer = self.layer
            run_duration = time.monotonic() - start_time
            self.log.log(logger.TestcaseEndLogEvent(name, self.layer, run_duration))
            return retval
        except Exception: #pylint: disable=broad-except
            # Cleanup is done by "with" handler __exit__
            traceback.print_exc()
            self.log.log(logger.TBotFinishedLogEvent(False))
            self.log.write_logfile()
            sys.exit(1)

    def machine(self,
                mach: tbot.machine.Machine,
                overwrite: bool = True) -> 'TBot':
        """
        Create a new TBot instance with a new machine

        :param mach: The machine to be added in the new instance
        :param overwrite: Whether overwriting an existing machine is allowed
        :returns: The new TBot instance, which has to be used inside a with
            statement
        """
        new_inst = TBot(self.config, self.testcases, self.log, False)
        new_inst.layer = self.layer
        new_inst.machines = tbot.machine.MachineManager(new_inst, self.machines.connection)

        for machine_name in self.machines.keys():
            new_inst.machines[machine_name] = self.machines[machine_name]

        if overwrite or not mach.common_machine_name in new_inst.machines:
            mach._setup(new_inst) #pylint: disable=protected-access
            new_inst.machines[mach.common_machine_name] = mach
            new_inst.machines[mach.unique_machine_name] = mach
            new_inst.destruct_machines.append(mach)
        return new_inst

    def with_boardshell(self) -> 'TBot':
        """
        Shortcut to create a new TBot instance with a boardmachine

        :returns: The new TBot instance, which has to be used inside a with
            statement
        """
        return self.machine(tbot.machine.MachineBoardRlogin(), overwrite=False)

    def __enter__(self) -> 'TBot':
        return self

    def destruct(self) -> None:
        """
        Destruct this TBot instance and all associated machines. This
        method will be called automatically when exiting a with statement.
        """
        # Make sure logfile is written
        self.log.write_logfile()
        # Destruct all machines that need to be destructed
        for mach in self.destruct_machines:
            if mach.common_machine_name == "board":
                self.log.log(logger.CustomLogEvent(
                    ["boardshell_cleanup"],
                    "\x1B[1mBOARD CLEANUP\x1B[0m",
                    logger.Verbosity.INFO))
            #pylint: disable=protected-access
            mach._destruct(self)

    def __exit__(self,
                 exc_type: typing.Any,
                 exc_value: typing.Any,
                 trceback: typing.Any) -> None:
        self.destruct()


def main() -> None:
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

    args = parser.parse_args()

    tbot_config_path = pathlib.PurePosixPath(args.confdir) / "tbot.toml"
    lab_config_path = pathlib.PurePosixPath(str(args.labconfdir).format(confdir=args.confdir)) \
        / f"{args.lab}.toml"
    board_config_path = pathlib.PurePosixPath(str(args.boardconfdir).format(confdir=args.confdir)) \
        / f"{args.board}.toml"

    config = config_parser.Config(list(map(str,
                                           [tbot_config_path,
                                            lab_config_path,
                                            board_config_path])))

    tbotpath = pathlib.Path(__file__).absolute().parent
    tc_paths = [str(path).format(tbotpath=tbotpath) for path in args.tcdir]
    testcases = testcase_collector.get_testcases(tc_paths)

    verbosity = logger.Verbosity(logger.Verbosity.INFO + len(args.verbose))
    log = logger.Logger(verbosity,
                        args.logfile)

    with TBot(config, testcases, log) as tb:
        # tb.log.log_info(f"LAB: {config.lab_name}")
        # tb.log.log_info(f"BOARD: {config.board_name}")

        if args.testcase is not None:
            tb.call(args.testcase)
        else:
            @tb.call
            def default(tb: TBot) -> None: #pylint: disable=unused-variable
                """ Default testcase is building U-Boot """
                tb.call("build_uboot")
        tb.log.log(logger.TBotFinishedLogEvent(True))
