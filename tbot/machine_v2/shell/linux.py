import contextlib
import typing
from . import shell

import time


class Bash(shell.Shell):
    @contextlib.contextmanager
    def _init_shell(self) -> typing.Iterator:
        try:
            time.sleep(0.5)

            yield None
        finally:
            pass

    def exec(self, *args: str) -> str:
        cmd = " ".join(args)
        self.ch.sendline(cmd)
        time.sleep(0.2)
        ret = self.ch.read()
        return ret.decode()

    def exec0(self, *args: str) -> str:
        return self.exec(*args)
