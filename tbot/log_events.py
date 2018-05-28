"""
TBot log events
---------------
"""
import typing
import tbot

RST = tbot.log.has_color("0")
BRED = tbot.log.has_color("1;31")
BGREEN = tbot.log.has_color("1;32")
BYELLOW = tbot.log.has_color("1;33")
BBLUE = tbot.log.has_color("1;34")

DASH_END = tbot.log.has_unicode("└─", "\\-")


def testcase_begin(name: str) -> tbot.log.LogStdoutHandler:
    """
    Log event for when a testcase is called

    :param name: Name of the testcase
    :type name: str
    :returns: A handler for the created log event
    :rtype: LogStdoutHandler
    """
    return tbot.log.event(
        ty=["testcase", "begin"],
        msg=f"Calling {BBLUE}{name}{RST} ...",
        verbosity=tbot.log.Verbosity.ALL,
        dct={"name": name},
    )


def testcase_end(
    name: str, duration: float, success: bool = True, fail_ok: bool = False
) -> tbot.log.LogStdoutHandler:
    """
    Log event for when a testcase is done

    :param name: Name of the testcase
    :type name: str
    :param duration: Duration of the testcase's execution
    :type duration: float (seconds)
    :param success: Whether the testcase was successful
    :type success: bool
    :param fail_ok: Whether a failure is acceptable for this testcase
    :type fail_ok: bool
    :returns: A handler for the created log event
    :rtype: LogStdoutHandler
    """
    if success:
        message = BGREEN + "Done."
    else:
        if fail_ok:
            message = BYELLOW + "Fail expected."
        else:
            message = BRED + "Fail."
    return tbot.log.event(
        ty=["testcase", "end"],
        msg=message,
        verbosity=tbot.log.Verbosity.ALL,
        dct={
            "name": name,
            "duration": duration,
            "success": success,
            "fail_ok": success,
        },
        custom_dash=DASH_END,
    )


def tbot_done(success: bool) -> tbot.log.LogStdoutHandler:
    """
    Log event for TBot being done with running testcases

    :param success: Whether this run of TBot was successful
    :type success: bool
    :returns: A handler for the created log event
    :rtype: LogStdoutHandler
    """
    message = (
        f"Done, {BGREEN if success else BRED}{'SUCCESS' if success else 'FAILURE'}"
    )
    return tbot.log.event(
        ty=["tbot", "end"],
        msg=message,
        verbosity=tbot.log.Verbosity.ALL,
        dct={"success": success},
        custom_dash=DASH_END,
    )


def exception(name: str, trace: str) -> tbot.log.LogStdoutHandler:
    """
    Log event for exceptions

    :param name: Name of the exception
    :type name: str
    :param trace: Traceback of the exception
    :type trace: str
    :returns: A handler for the created log event
    :rtype: LogStdoutHandler
    """
    return tbot.log.event(
        ty=["exception"],
        msg=f"Catched exception: {name}",
        verbosity=tbot.log.Verbosity.DEBUG,
        dct={"name": name, "trace": trace},
    )


def shell_command(
    *, machine: typing.List[str], command: str, show: bool, show_stdout: bool
) -> tbot.log.LogStdoutHandler:
    """
    Log event for the execution of shell commands

    Add output of the command by calling the ``print`` method of
    the event handler. When the command is done, set the exit code.

    **Example**::

        handler = tbot.log_events.shell_command(
            machine=["labhost", "env"],
            command="echo Hello World",
            show=True,
            show_stdout=True,
        )

        # Print the output of the command
        handler.print("Hello World\\n")

        # Set exit code
        handler.dct["exit_code"] = 0


    :param machine: Unique name of the machine as a list
    :type machine: list[str]
    :param command: The command that was executed itself
    :type command: str
    :param show: Whether this command should be shown in documentation
    :type show: bool
    :param show_stdout: Whether this commands output should be shown in
                        documentation
    :type show_stdout: bool
    :returns: A handler for the created log event
    :rtype: LogStdoutHandler
    """
    machine_string = "("
    for i in range(0, len(machine) - 1):
        machine_string += machine[i] + ", "
    machine_string += machine[-1] + ")"
    cmd = repr(command)[1:-1]
    ty = ["shell"]
    ty.extend(machine)
    handler = tbot.log.event(
        ty=ty,
        msg=f"{machine_string} {cmd}",
        verbosity=tbot.log.Verbosity.VERBOSE,
        dct={
            "command": command,
            "show": show,
            "show_stdout": show_stdout,
            "output": "",
        },
    )

    handler.reset_verbosity(tbot.log.Verbosity.VERY_VERBOSE)
    handler.prefix = "   ## "
    handler.key = "output"
    return handler
