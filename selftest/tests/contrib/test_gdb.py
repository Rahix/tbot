import re
from typing import Tuple, Type

import pytest
import testmachines

import tbot
import tbot_contrib.gdb
from tbot.machine import linux

RESULT_PATTERN = re.compile(r"\$\d+ = 0x[0-9a-f]+ (?:<.*> )?\"(.*)\"")


@pytest.mark.parametrize(  # type: ignore
    "failure_mode",
    [
        ("true", linux.CommandEndedException),
        ("false", tbot.error.CommandFailure),
    ],
    ids=lambda failure_mode: failure_mode[1].__name__,
)
def test_gdb_start_crash(
    tbot_context: tbot.Context, failure_mode: Tuple[str, Type[Exception]]
) -> None:
    command, exception = failure_mode
    with tbot_context.request(testmachines.Localhost) as lh:
        with pytest.raises(exception):
            # Run `echo` instead of GDB to force an initialization error
            with tbot_contrib.gdb.GDB(lh, gdb=command) as gdb:
                gdb.exec("help")

        lh.exec0("uname", "-r")


def test_gdb_init_hang(tbot_context: tbot.Context) -> None:
    with tbot_context.request(testmachines.Localhost) as lh:
        with pytest.raises(TimeoutError):
            # Run `echo` instead of GDB to force and hack in a sleep
            # to let the initialization hang forever
            with tbot_contrib.gdb.GDB(lh, linux.Then, "sleep", "30", gdb="echo") as gdb:  # type: ignore
                gdb.exec("help")

        lh.exec0("uname", "-r")


def test_gdb_machine(tbot_context: tbot.Context) -> None:
    with tbot_context.request(testmachines.Localhost) as lh:
        program = lh.exec0("which", "echo").strip()

        if not lh.test("which", "gdb"):
            pytest.skip("GDB is missing.")

        with tbot_contrib.gdb.GDB(lh, program) as gdb:
            out = gdb.exec("break", "getenv")
            if "not defined" in out or "No symbol table" in out:
                pytest.skip("Debug symbols missing.")
            gdb.exec("run", "hello", "world")

            while True:
                # First argument is in RDI
                out = gdb.exec("print", "(char*)($rdi)").strip()
                match = RESULT_PATTERN.match(out)
                assert match is not None
                val = match.group(1)
                tbot.log.message(
                    f'{program}: {tbot.log.c("getenv").green}("{tbot.log.c(val).bold}")'
                )

                if "exited" in gdb.exec("continue"):
                    break

        lh.exec0("echo", "back out of gdb!")
