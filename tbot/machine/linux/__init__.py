import abc
import typing
import shlex
from tbot import log
from tbot import machine
from tbot.machine import channel
from tbot.machine.linux.path import Path


class LinuxMachine(machine.Machine):
    @property
    @abc.abstractmethod
    def username(self) -> str:
        """Return the username for logging in on this machine."""
        pass

    @property
    @abc.abstractmethod
    def workdir(self) -> Path:
        """Return a path where testcases can store data on this host."""
        pass

    @abc.abstractmethod
    def _obtain_channel(self) -> channel.Channel:
        pass

    def build_command(
        self,
        *args: typing.Union[str, Path],
        stdout: typing.Optional[Path] = None,
    ) -> str:
        """
        Build the string representation of a command.

        :param args: Each arg is a token that will be sent to the shell. Can be
                     either a str or a Path that is associated with this
                     host. Arguments will be escaped (a str like "a b" will not
                     result in separate arguments to the command)
        :param Path stdout: File where stdout should be directed to
        :returns: A string that would be sent to the machine to execute the command
        :rtype: str
        """
        command = ""
        for arg in args:
            if isinstance(arg, Path):
                if arg.host is not self:
                    raise Exception(f"{self!r}: Provided {arg!r} is not associated with this host")

                arg = arg._local_str()

            command += f"{shlex.quote(arg)} "

        if isinstance(stdout, Path):
            if stdout.host is not self:
                raise Exception(f"{self!r}: Provided {stdout!r} is not associated with this host")
            stdout_file = stdout._local_str()
            command += f">{shlex.quote(stdout_file)}"

        return command

    def exec(
        self,
        *args: typing.Union[str, Path],
        stdout: typing.Optional[Path] = None,
    ) -> typing.Tuple[int, str]:
        """
        Run a command on this machine.

        :param args: Each arg is a token that will be sent to the shell. Can be
                     either a str or a Path that is associated with this
                     host. Arguments will be escaped (a str like "a b" will not
                     result in separate arguments to the command)
        :param Path stdout: File where stdout should be directed to
        :returns: Tuple with the exit code and a string containing the combined
                  stdout and stderr of the command (with a trailing newline).
        :rtype: (int, str)
        """
        channel = self._obtain_channel()

        command = self.build_command(*args, stdout=stdout)

        ev = log.command(self.name, command)

        ret, out = channel.raw_command_with_retval(command, stream=ev)

        return ret, out

    def exec0(
        self,
        *args: typing.Union[str, Path],
        stdout: typing.Optional[Path] = None,
    ) -> str:
        """
        Run a command on this machine and ensure it succeeds.

        :param args: Each arg is a token that will be sent to the shell. Can be
                     either a str or a Path that is associated with this
                     host. Arguments will be escaped (a str like "a b" will not
                     result in separate arguments to the command)
        :param Path stdout: File where stdout should be directed to
        :returns: A string containing the combined stdout and stderr of the
                  command (with a trailing newline).
        :rtype: str
        """
        ret, out = self.exec(*args, stdout=stdout)
        assert ret == 0, "Command failed!"
        return out
