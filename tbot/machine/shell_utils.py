"""
Utilities for shell interaction
"""
import typing
import re
import paramiko
import tbot

def setup_channel(chan: paramiko.Channel,
                  prompt: str) -> None:
    """
    Setup a paramiko channel

    :param chan: The channel to be set up
    :type chan: paramiko.Channel
    :param prompt: The prompt that should be used, has to be very unique!
    :type prompt: str
    :returns: Nothing
    :rtype: None
    """
    chan.get_pty("xterm-256color")
    # Resize the pty to ensure we do not get escape sequences from the terminal
    # trying to wrap to the next line
    chan.resize_pty(200, 200, 1000, 1000)
    chan.invoke_shell()

    # Initialize remote shell
    chan.send(f"""\
unset HISTFILE
PROMPT_COMMAND=''
PS1='{prompt}'
""")

    read_to_prompt(chan, prompt)

def read_to_prompt(chan: paramiko.Channel,
                   prompt: str,
                   stdout_handler = None,
                   prompt_regex: bool = False,
                  ) -> str:
    """
    Read until the shell waits for further input

    :param chan: Channel to read from
    :type chan: paramiko.Channel
    :param prompt: Prompt to be waited for
    :type prompt: str
    :param log_event: Optional log event to write output lines to
    :type log_event: tbot.logger.LogEvent
    :returns: The read string (including the prompt)
    :param prompt_regex: Wether the prompt string is to be interpreted as
                         a regular expression (read_to_prompt will add a $
                         to the end of your expression to ensure it only
                         matches the end of the output)
    :type prompt_regex: bool
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
        buf_data = buf_data.replace('\r\n', '\n') \
            .replace('\r\n', '\n') \
            .replace('\r', '\n')

        buf += buf_data

        tbot.log.oververbose(repr(buf_data))

        if stdout_handler is not None:
            while "\n" in buf[last_newline:]:
                line = buf[last_newline:].split('\n')[0]
                if last_newline != 0:
                    stdout_handler.print(line)
                last_newline += len(line) + 1

        if (not prompt_regex and buf[-len(prompt):] == prompt) \
            or (prompt_regex and re.search(expression, buf) is not None):
            # Print rest of last line to make sure nothing gets lost
            if stdout_handler is not None and "\n" not in buf[last_newline:]:
                line = buf[last_newline:-len(prompt)]
                if line != "":
                    stdout_handler.print(line)
            break

    return buf

def exec_command(chan: paramiko.Channel,
                 prompt: str,
                 command: str,
                 stdout_handler = None) -> str:
    """
    Execute a command and return it's output

    :param chan: Channel to execute this command on
    :type chan: paramiko.Channel
    :param prompt: Prompt to be expected
    :type prompt: str
    :param command: Command to be executed (no trailing ``\\n``)
    :type command: str
    :param log_event: Optional log event for this command
    :type log_event: tbot.logger.LogEvent
    :returns: The output of the command
    :rtype: str
    """
    chan.send(f"{command}\n")
    stdout = read_to_prompt(
        chan,
        prompt,
        stdout_handler,
    )[len(command)+1:-len(prompt)]

    return stdout

def command_and_retval(chan: paramiko.Channel,
                       prompt: str,
                       command: str,
                       stdout_handler = None,
                      ) -> typing.Tuple[int, str]:
    """
    Execute a command and return it's output and return value

    :param chan: Channel to execute this command on
    :type chan: paramiko.Channel
    :param prompt: Prompt to be expected
    :type prompt: str
    :param command: Command to be executed (no trailing ``\\n``)
    :type command: str
    :param log_event: Optional log event for this command
    :type log_event: tbot.logger.LogEvent
    :returns: The return-code and output of the command
    :rtype: tuple[int, str]
    """
    stdout = exec_command(chan, prompt, command, stdout_handler)

    # Get the return code
    retcode = int(exec_command(chan, prompt, "echo $?", None).strip())

    return retcode, stdout
