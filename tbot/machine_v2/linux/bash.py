import contextlib
import re
import shlex
import shutil
import typing

import tbot
from . import linux_shell, util, special, path

TBOT_PROMPT = b"TBOT-VEJPVC1QUk9NUFQK$ "


class Bash(linux_shell.LinuxShell):
    @contextlib.contextmanager
    def _init_shell(self) -> typing.Iterator:
        try:
            # Wait for shell to appear
            util.wait_for_shell(self.ch)

            # Set prompt to a known string
            self.ch.sendline(b"PROMPT_COMMAND=''; PS1='" + TBOT_PROMPT + b"'")
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

            yield None
        finally:
            pass

    def escape(self, *args: linux_shell.ArgTypes) -> str:
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

    def exec(self, *args: linux_shell.ArgTypes) -> typing.Tuple[int, str]:
        cmd = self.escape(*args)

        with tbot.log_event.command(self.name, cmd) as ev:
            self.ch.sendline(cmd, read_back=True)
            with self.ch.with_stream(ev, show_prompt=False):
                out = self.ch.read_until_prompt()

            self.ch.sendline("echo $?", read_back=True)
            retcode = self.ch.read_until_prompt()

        return (int(retcode), out)

    def exec0(self, *args: linux_shell.ArgTypes) -> str:
        retcode, out = self.exec(*args)
        if retcode != 0:
            raise Exception(f"command {args!r} failed")
        return out

    def test(self, *args: linux_shell.ArgTypes) -> bool:
        retcode, _ = self.exec(*args)
        return retcode == 0

    def env(self, var: str, value: typing.Optional[linux_shell.ArgTypes] = None) -> str:
        if value is not None:
            self.exec0(
                "export", special.Raw(f"{self.escape(var)}={self.escape(value)}")
            )

        return self.exec0("echo", special.Raw(f'"${{{self.escape(var)}}}"'))[:-1]

    @contextlib.contextmanager
    def subshell(self) -> "typing.Iterator[Bash]":
        tbot.log_event.command(self.name, "bash --norc")
        self.ch.sendline("bash --norc")
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
        self.ch.sendline(f"bash --norc")
        self.ch.sendline(f"PS1={endstr}")
        self.ch.read_until_prompt(prompt=endstr)

        # Inner shell which will be used by the user
        self.ch.sendline("bash --norc")
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
