"""
Utilities for shell interaction
"""
import typing
import re
import paramiko
import tbot


class InvalidChannelState(Exception):
    """ An invalid channel state """
    pass


class InvalidCommand(Exception):
    """ An invalid channel state """
    pass


def setup_channel(chan: paramiko.Channel, prompt: str) -> None:
    """
    Setup a paramiko channel

    :param paramiko.channel.Channel chan: The channel to be set up
    :param str prompt: The prompt that should be used, has to be very unique!
    :returns: Nothing
    :rtype: None
    """
    chan.get_pty("xterm-256color")
    # Resize the pty to ensure we do not get escape sequences from the terminal
    # trying to wrap to the next line
    chan.resize_pty(200, 200, 1000, 1000)
    chan.invoke_shell()

    # Initialize remote shell
    chan.send(
        f"""\
unset HISTFILE
PROMPT_COMMAND=''
PS1='{prompt}'
"""
    )

    read_to_prompt(chan, prompt)


def read_to_prompt(
    chan: paramiko.Channel,
    prompt: str,
    stdout_handler: typing.Optional[tbot.log.LogStdoutHandler] = None,
    prompt_regex: bool = False,
) -> str:
    """
    Read until the shell waits for further input

    :param paramiko.channel.Channel chan: Channel to read from
    :param str prompt: Prompt to be waited for
    :param tbot.log.LogStdoutHandler stdout_handler: Optional stdout handler to write output lines to
    :param bool prompt_regex: Wether the prompt string is to be interpreted as
                         a regular expression (read_to_prompt will add a $
                         to the end of your expression to ensure it only
                         matches the end of the output)
    :returns: The read string (including the prompt)
    :rtype: str
    """
    buf = ""

    expression = f"{prompt}$" if prompt_regex else "^$"

    last_newline = 0

    while True:
        # Read a lot and hope that this is all there is, so
        # we don't cut off inside a unicode sequence and fail
        buf_data = chan.recv(10000000)
        try:
            buf_data = buf_data.decode("utf-8")
        except UnicodeDecodeError:
            # Fall back to latin-1 if unicode decoding fails ... This is not perfect
            # but it does not stop a test run just because of an invalid character
            buf_data = buf_data.decode("latin_1")

        # Fix '\r's, replace '\r\n' twice to avoid some glitches
        buf_data = (
            buf_data.replace("\r\n", "\n").replace("\r\n", "\n").replace("\r", "\n")
        )

        buf += buf_data

        tbot.log.oververbose(repr(buf_data))

        if stdout_handler is not None:
            while "\n" in buf[last_newline:]:
                line = buf[last_newline:].split("\n")[0]
                if last_newline != 0:
                    stdout_handler.print(line)
                last_newline += len(line) + 1

        if (not prompt_regex and buf[-len(prompt) :] == prompt) or (
            prompt_regex and re.search(expression, buf) is not None
        ):
            # Print rest of last line to make sure nothing gets lost
            if stdout_handler is not None and "\n" not in buf[last_newline:]:
                line = buf[last_newline : -len(prompt)]
                if line != "":
                    stdout_handler.print(line)
            break

        # Check if the channel has been closed
        if buf_data == "" and chan.exit_status_ready():
            return buf

    return buf


def exec_command(
    chan: paramiko.Channel,
    prompt: str,
    command: str,
    stdout_handler: typing.Optional[tbot.log.LogStdoutHandler] = None,
) -> str:
    """
    Execute a command and return it's output

    :param paramiko.channel.Channel chan: Channel to execute this command on
    :param str prompt: Prompt to be expected
    :param str command: Command to be executed (no trailing ``\\n``)
    :param tbot.log.LogStdoutHandler stdout_handler: Optional stdout handler to write output lines to
    :returns: The output of the command
    :rtype: str
    """
    if "\n" in command:
        raise InvalidCommand(
            f"""{command!r} contains a '\\n', which is not allowed.
    Use multiple calls or a ';' to call multiple commands"""
        )
    if chan.exit_status_ready():
        raise InvalidChannelState("Trying to execute command on a closed channel")
    chan.send(f"{command}\n")
    stdout = read_to_prompt(chan, prompt, stdout_handler)[
        len(command) + 1 : -len(prompt)
    ]

    return stdout


def command_and_retval(
    chan: paramiko.Channel,
    prompt: str,
    command: str,
    stdout_handler: typing.Optional[tbot.log.LogStdoutHandler] = None,
) -> typing.Tuple[int, str]:
    """
    Execute a command and return it's output and return value

    :param paramiko.channel.Channel chan: Channel to execute this command on
    :param str prompt: Prompt to be expected
    :param str command: Command to be executed (no trailing ``\\n``)
    :param tbot.log.LogStdoutHandler stdout_handler: Optional stdout handler to write output lines to
    :returns: The return-code and output of the command
    :rtype: tuple[int, str]
    """
    stdout = exec_command(chan, prompt, command, stdout_handler)

    # Get the return code
    retcode = int(exec_command(chan, prompt, "echo $?", None).strip())

    return retcode, stdout
