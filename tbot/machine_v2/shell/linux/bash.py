import contextlib
import shlex
import typing

import tbot
from . import linux_shell, util

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

    def build_command(self, *args: str) -> str:
        string_args = []
        for arg in args:
            if isinstance(arg, str):
                string_args.append(shlex.quote(arg))
            else:
                raise TypeError("{arg!r} is not of a supported argument type!")

        return " ".join(string_args)

    def exec(self, *args: str) -> typing.Tuple[int, str]:
        cmd = self.build_command(*args)

        with tbot.log_event.command(self.name, cmd) as ev:
            self.ch.sendline(cmd, read_back=True)
            with self.ch.with_stream(ev, show_prompt=False):
                out = self.ch.read_until_prompt()

            self.ch.sendline("echo $?", read_back=True)
            retcode = self.ch.read_until_prompt()

        return (int(retcode), out)

    def exec0(self, *args: str) -> str:
        retcode, out = self.exec(*args)
        if retcode != 0:
            raise Exception(f"command {args!r} failed")
        return out
