import contextlib
import re
import shlex
import typing

import tbot
from .. import shell, machine
from ..linux import special


class UBootAutobootIntercept(machine.Initializer):
    autoboot_prompt = re.compile(b"autoboot:\\s{0,5}\\d{0,3}\\s{0,3}.{0,80}")

    autoboot_keys: typing.Union[str, bytes] = "\r"

    @contextlib.contextmanager
    def _init_machine(self) -> typing.Iterator:
        self.ch.read_until_prompt(prompt=self.autoboot_prompt)
        self.ch.send(self.autoboot_keys)

        yield None


ArgTypes = typing.Union[str, special.Special]


class UBootShell(shell.Shell):
    prompt: typing.Union[str, bytes] = "U-Boot> "

    @contextlib.contextmanager
    def _init_shell(self) -> typing.Iterator:
        self.ch.prompt = (
            self.prompt.encode("utf-8") if isinstance(self.prompt, str) else self.prompt
        )

        while True:
            try:
                self.ch.read_until_prompt(timeout=0.2)
                break
            except TimeoutError:
                self.ch.sendintr()

        yield None

    def escape(self, *args: ArgTypes) -> str:
        string_args = []
        for arg in args:
            if isinstance(arg, str):
                string_args.append(shlex.quote(arg))
            elif isinstance(arg, special.Special):
                string_args.append(arg._to_string(self))
            else:
                raise TypeError(f"{type(arg)!r} is not a supported argument type!")

        return " ".join(string_args)

    def exec(self, *args: ArgTypes) -> typing.Tuple[int, str]:
        cmd = self.escape(*args)

        with tbot.log_event.command(self.name, cmd) as ev:
            self.ch.sendline(cmd, read_back=True)
            with self.ch.with_stream(ev, show_prompt=False):
                out = self.ch.read_until_prompt()

            self.ch.sendline("echo $?", read_back=True)
            retcode = self.ch.read_until_prompt()

        return (int(retcode), out)

    def exec0(self, *args: ArgTypes) -> str:
        retcode, out = self.exec(*args)
        if retcode != 0:
            cmd = self.escape(*args)
            raise Exception(f"command {cmd!r} failed")
        return out

    def test(self, *args: ArgTypes) -> bool:
        retcode, _ = self.exec(*args)
        return retcode == 0

    def env(self, var: str, value: typing.Optional[ArgTypes] = None) -> str:
        if value is not None:
            self.exec0(
                "export", special.Raw(f"{self.escape(var)}={self.escape(value)}")
            )

        return self.exec0("echo", special.Raw(f'"${{{self.escape(var)}}}"'))[:-1]

    def interactive(self) -> None:
        tbot.log.message("Entering interactive shell (CTRL+D to exit) ...")

        # It is important to send a space before the newline.  Otherwise U-Boot
        # will reexecute the last command which we definitely do not want here.
        self.ch.sendline(" ")
        self.ch.attach_interactive()
        print("")
        self.ch.sendline(" ")

        try:
            self.ch.read_until_prompt(timeout=0.5)
        except TimeoutError:
            raise Exception("Failed to reacquire U-Boot after interactive session!")

        tbot.log.message("Exiting interactive shell ...")
