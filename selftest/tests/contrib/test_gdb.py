import re

import pytest
import testmachines

import tbot
import tbot_contrib.gdb

RESULT_PATTERN = re.compile(r"\$\d+ = 0x[0-9a-f]+ (?:<.*> )?\"(.*)\"")


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
