"""
TBot
----
"""
import time
import pathlib
import typing
import traceback
import sys
import paramiko
import enforce
from tbot import config_parser
from tbot import log
from tbot import log_events
from tbot import testcase_collector
from tbot import tc
import tbot.machine
import tbot.config

from tbot.testcase_collector import testcase

#pylint: disable=too-many-instance-attributes
class TBot:
    """
    Main class of TBot, you usually do not need to instanciate this yourself

    :param config: A configuration to be used
    :type config: tbot.config.Config
    :param testcases: Testcases available to this instance
    :type testcases: dict
    :param new: Whether this is a new instance that should create a noenv machine.
        Always ``True`` unless you know what you are doing.
    :type new: bool
    :ivar config: :class:`tbot.config.Config()`
    :ivar testcases: All available testcases
    :ivar machines: All available machines :class:`tbot.machine.machine.MachineManager()`
    """
    def __init__(self,
                 config: tbot.config.Config,
                 testcases: dict,
                 new: bool = True) -> None:
        self.config = config
        self.testcases = testcases
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
        :type tc: str or typing.Callable
        :param kwargs: Additional arguments for the testcase
        :type kwargs: dict
        :returns: The decorated function
        :rtype: typing.Callable
        """
        def _decorator(f: typing.Callable) -> typing.Any:
            kwargs["and_then"] = f
            self.call(tc, **kwargs)
            return f
        return _decorator

    def call(self, tc: typing.Union[str, typing.Callable], *,
             fail_ok: bool = False,
             **kwargs: typing.Any) -> typing.Any:
        """
        Call a testcase

        :param tc: The testcase to be called. Can either be a string or a callable
        :type tc: str or typing.Callable
        :param fail_ok: Whether a failure in this testcase is tolerable
        :type fail_ok: bool
        :param kwargs: Additional arguments for the testcase
        :type kwargs: dict
        :returns: The return value from the testcase
        """
        name = tc if isinstance(tc, str) else f"@{tc.__name__}"
        tbot.log_events.testcase_begin(name)
        self.layer += 1
        tbot.log.set_layer(self.layer)
        start_time = time.monotonic()

        try:
            if isinstance(tc, str):
                retval = self.testcases[tc](self, **kwargs)
            else:
                retval = enforce.runtime_validation(tc)(self, **kwargs)
        except Exception as e: #pylint: disable=broad-except
            # Cleanup is done by "with" handler __exit__
            # A small hack to ensure, the exception is only added once:
            if "__tbot_exc_catched" not in e.__dict__:
                exc_name = type(e).__module__ + "." + type(e).__qualname__
                tbot.log_events.exception(exc_name, traceback.format_exc())
                e.__dict__["__tbot_exc_catched"] = True
            self.layer -= 1
            run_duration = time.monotonic() - start_time
            tbot.log_events.testcase_end(name, run_duration, False, fail_ok)
            tbot.log.set_layer(self.layer)
            raise

        self.layer -= 1
        run_duration = time.monotonic() - start_time
        tbot.log_events.testcase_end(name, run_duration, True)
        tbot.log.set_layer(self.layer)
        return retval

    def machine(self,
                mach: tbot.machine.Machine) -> 'TBot':
        """
        Create a new TBot instance with a new machine

        :param mach: The machine to be added in the new instance
        :type mach: tbot.machine.machine.Machine
        :returns: The new TBot instance, which has to be used inside a with
            statement
        :rtype: TBot
        """
        new_inst = TBot(self.config, self.testcases, False)
        new_inst.layer = self.layer
        new_inst.machines = tbot.machine.MachineManager(new_inst, self.machines.connection)

        for machine_name in self.machines.keys():
            new_inst.machines[machine_name] = self.machines[machine_name]

        old_mach = new_inst.machines[mach.common_machine_name] \
            if mach.common_machine_name in new_inst.machines else \
            None
        new_mach = mach._setup(new_inst, old_mach) #pylint: disable=protected-access
        new_inst.machines[mach.common_machine_name] = new_mach
        new_inst.machines[mach.unique_machine_name] = new_mach
        if new_mach is not old_mach:
            new_inst.destruct_machines.append(new_mach)
        return new_inst

    def with_board_uboot(self) -> 'TBot':
        """
        Shortcut to create a new TBot instance with a U-Boot boardmachine

        :returns: The new TBot instance, which has to be used inside a with
            statement
        :rtype: TBot
        """
        return self.machine(tbot.machine.MachineBoardUBoot())

    def with_board_linux(self) -> 'TBot':
        """
        Shortcut to create a new TBot instance with a Linux boardmachine

        :returns: The new TBot instance, which has to be used inside a with
            statement
        :rtype: TBot
        """
        return self.machine(tbot.machine.MachineBoardLinux())

    def __enter__(self) -> 'TBot':
        return self

    def destruct(self) -> None:
        """
        Destruct this TBot instance and all associated machines. This
        method will be called automatically when exiting a with statement.
        """
        # Make sure logfile is written
        tbot.log.flush_log()
        # Destruct all machines that need to be destructed
        for mach in self.destruct_machines:
            #pylint: disable=protected-access
            mach._destruct(self)

    def __exit__(self,
                 exc_type: typing.Any,
                 exc_value: typing.Any,
                 trceback: typing.Any) -> None:
        self.destruct()
