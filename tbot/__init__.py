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
import argcomplete
from tbot import config_parser
from tbot import logger
from tbot import testcase_collector
import tbot.machine
import tbot.config

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
                 config: tbot.config.Config,
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
            #pylint: disable=protected-access
            mach._destruct(self)

    def __exit__(self,
                 exc_type: typing.Any,
                 exc_value: typing.Any,
                 trceback: typing.Any) -> None:
        self.destruct()
