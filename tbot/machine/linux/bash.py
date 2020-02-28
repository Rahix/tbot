# tbot, Embedded Automation Tool
# Copyright (C) 2019  Harald Seiler
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import contextlib
import re
import shlex
import shutil
import typing

import tbot
from .. import channel
from . import linux_shell, util, special, path

TBOT_PROMPT = b"TBOT-VEJPVC1QUk9NUFQK$ "

Self = typing.TypeVar("Self", bound="Bash")


class Bash(linux_shell.LinuxShell):
    """Bourne-again shell."""

    @contextlib.contextmanager
    def _init_shell(self) -> typing.Iterator:
        try:
            # Wait for shell to appear
            util.wait_for_shell(self.ch)

            # Set prompt to a known string
            #
            # `read_back=True` is needed here so the following
            # read_until_prompt() will not accidentally detect the prompt in
            # the sent command if the connection is slow.
            #
            # To safeguard the process even further, the prompt is mangled in a
            # way which will be unfolded by the shell.  This will ensure tbot
            # won't accidentally read the prompt back early.
            self.ch.sendline(
                b"PROMPT_COMMAND=''; PS1='"
                + TBOT_PROMPT[:6]
                + b"''"
                + TBOT_PROMPT[6:]
                + b"'",
                read_back=True,
            )
            self.ch.prompt = TBOT_PROMPT
            self.ch.read_until_prompt()

            # Disable history
            self.ch.sendline("unset HISTFILE")
            self.ch.read_until_prompt()

            # Disable line editing
            self.ch.sendline("set +o emacs; set +o vi")
            self.ch.read_until_prompt()

            # Set secondary prompt to ""
            self.ch.sendline("PS2=''")
            self.ch.read_until_prompt()

            # Disable history expansion because it is not always affected by
            # quoting rules and thus can mess with parameter values.  For
            # example, m.exec0("echo", "\n^") triggers the 'quick substitution'
            # feature and will return "\n!!:s^\n" instead of the expected
            # "\n^\n".  As it is not really useful for tbot tests anyway,
            # disable all history expansion 'magic characters' entirely.
            self.ch.sendline("histchars=''")
            self.ch.read_until_prompt()

            # Set terminal size
            termsize = shutil.get_terminal_size()
            self.ch.sendline(f"stty cols {max(40, termsize.columns - 48)}")
            self.ch.read_until_prompt()
            self.ch.sendline(f"stty rows {termsize.lines}")
            self.ch.read_until_prompt()

            yield None
        finally:
            pass

    def escape(
        self: Self, *args: typing.Union[str, special.Special[Self], path.Path[Self]]
    ) -> str:
        string_args = []
        for arg in args:
            if isinstance(arg, str):
                string_args.append(shlex.quote(arg))
            elif isinstance(arg, linux_shell.Special):
                string_args.append(arg._to_string(self))
            elif isinstance(arg, path.Path):
                if arg.host is not self:
                    raise Exception("{arg!r} is for another host!")
                string_args.append(shlex.quote(arg._local_str()))
            else:
                raise TypeError(f"{type(arg)!r} is not a supported argument type!")

        return " ".join(string_args)

    def exec(
        self: Self, *args: typing.Union[str, special.Special[Self], path.Path[Self]]
    ) -> typing.Tuple[int, str]:
        cmd = self.escape(*args)

        with tbot.log_event.command(self.name, cmd) as ev:
            self.ch.sendline(cmd, read_back=True)
            with self.ch.with_stream(ev, show_prompt=False):
                out = self.ch.read_until_prompt()
            ev.data["stdout"] = out

            self.ch.sendline("echo $?", read_back=True)
            retcode = self.ch.read_until_prompt()

        return (int(retcode), out)

    def exec0(
        self: Self, *args: typing.Union[str, special.Special[Self], path.Path[Self]]
    ) -> str:
        retcode, out = self.exec(*args)
        if retcode != 0:
            cmd = self.escape(*args)
            raise Exception(f"command {cmd!r} failed")
        return out

    def test(
        self: Self, *args: typing.Union[str, special.Special[Self], path.Path[Self]]
    ) -> bool:
        retcode, _ = self.exec(*args)
        return retcode == 0

    def env(
        self: Self, var: str, value: typing.Union[str, path.Path[Self], None] = None
    ) -> str:
        if value is not None:
            self.exec0(
                "export", special.Raw(f"{self.escape(var)}={self.escape(value)}")
            )

        # Add a space in front of the expanded environment variable to ensure
        # values like `-E` will not get picked up as parameters by echo.  This
        # space is then cut away again so calling tests don't notice this trick.
        return self.exec0("echo", special.Raw(f'" ${{{self.escape(var)}}}"'))[1:-1]

    def open_channel(
        self: Self, *args: typing.Union[str, special.Special[Self], path.Path[Self]]
    ) -> channel.Channel:
        cmd = self.escape(*args)

        # Disable the interrupt key in the outer shell
        self.ch.sendline("stty -isig", read_back=True)
        self.ch.read_until_prompt()

        with tbot.log_event.command(self.name, cmd):
            # Append `; exit` to ensure the channel won't live past the command
            # exiting
            self.ch.sendline(cmd + "; exit", read_back=True)

        return self.ch.take()

    @contextlib.contextmanager
    def subshell(
        self: Self, *args: typing.Union[str, special.Special[Self], path.Path[Self]]
    ) -> "typing.Iterator[Bash]":
        if args == ():
            cmd = "bash --norc --noprofile"
        else:
            cmd = self.escape(*args)
        tbot.log_event.command(self.name, cmd)
        self.ch.sendline(cmd)

        try:
            with self._init_shell():
                yield self
        finally:
            self.ch.sendline("exit")
            self.ch.read_until_prompt()

    def interactive(self) -> None:
        # Generate the endstring instead of having it as a constant
        # so opening this files won't trigger an exit
        endstr = (
            "INTERACTIVE-END-"
            + hex(165_380_656_580_165_943_945_649_390_069_628_824_191)[2:]
        )

        termsize = shutil.get_terminal_size()
        self.ch.sendline(self.escape("stty", "cols", str(termsize.columns)))
        self.ch.sendline(self.escape("stty", "rows", str(termsize.lines)))

        # Outer shell which is used to detect the end of the interactive session
        self.ch.sendline(f"bash --norc --noprofile")
        self.ch.sendline(f"PS1={endstr}")
        self.ch.read_until_prompt(prompt=endstr)

        # Inner shell which will be used by the user
        self.ch.sendline("bash --norc --noprofile")
        self.ch.sendline("set -o emacs")
        prompt = self.escape(
            f"\\[\\033[36m\\]{self.name}: \\[\\033[32m\\]\\w\\[\\033[0m\\]> "
        )
        self.ch.sendline(f"PS1={prompt}")

        self.ch.read_until_prompt(prompt=re.compile(b"> (\x1B\\[.{0,10})?"))
        self.ch.sendline()
        tbot.log.message("Entering interactive shell ...")

        self.ch.attach_interactive(end_magic=endstr)

        tbot.log.message("Exiting interactive shell ...")

        try:
            self.ch.sendline("exit")
            self.ch.read_until_prompt(timeout=0.5)
        except TimeoutError:
            raise Exception("Failed to reacquire shell after interactive session!")
