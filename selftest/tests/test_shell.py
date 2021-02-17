import pytest
from tbot.machine import linux
from tbot.tc import shell
from conftest import AnyLinuxShell


def test_simple_output(any_linux_shell: AnyLinuxShell) -> None:
    with any_linux_shell() as linux_shell:
        out = linux_shell.exec0("echo", "Hello World")
        assert out == "Hello World\n"

        out = linux_shell.exec0("echo", "$?", "!#")
        assert out == "$? !#\n"


def test_simple_printf(any_linux_shell: AnyLinuxShell) -> None:
    with any_linux_shell() as linux_shell:
        if not shell.check_for_tool(linux_shell, "printf"):
            pytest.skip("`printf` missing on this shell")

        out = linux_shell.exec0("printf", "Hello World")
        assert out == "Hello World"

        out = linux_shell.exec0("printf", "Hello\\nWorld")
        assert out == "Hello\nWorld"

        out = linux_shell.exec0("printf", "Hello\nWorld")
        assert out == "Hello\nWorld"


def test_long_output(any_linux_shell: AnyLinuxShell) -> None:
    with any_linux_shell() as linux_shell:
        s = "_".join(map(lambda i: f"{i:02}", range(80)))
        out = linux_shell.exec0("echo", s)
        assert out == f"{s}\n", repr(out)


def test_return_code(any_linux_shell: AnyLinuxShell) -> None:
    with any_linux_shell() as linux_shell:
        assert linux_shell.test("true")
        assert not linux_shell.test("false")

        for i in range(256):
            ret = linux_shell.exec("sh", "-c", f"exit {i}")[0]
            assert ret == i


def test_simple_environment(any_linux_shell: AnyLinuxShell) -> None:
    with any_linux_shell() as linux_shell:
        value = "12\nfoo !? # true; exit\n"
        linux_shell.env("TBOT_TEST_ENV_VAR", value)
        out = linux_shell.env("TBOT_TEST_ENV_VAR")
        assert out == value, repr(out)


def test_redirection(any_linux_shell: AnyLinuxShell) -> None:
    with any_linux_shell() as linux_shell:
        f = linux_shell.workdir / ".redir test.txt"
        if f.exists():
            linux_shell.exec0("rm", f)

        linux_shell.exec0("echo", "Some data - And some more", linux.RedirStdout(f))

        out = f.read_text()
        assert out == "Some data - And some more\n"


def test_subshell(any_linux_shell: AnyLinuxShell) -> None:
    with any_linux_shell() as linux_shell:
        # Only on the localhost because the "ash" hack is currently not working
        linux_shell.env("TBOT_SUBSHELL_TEST", "NUMBER_ONE")
        with linux_shell.subshell():
            linux_shell.env("TBOT_SUBSHELL_TEST", "SECOND_PLACE")
            with linux_shell.subshell():
                linux_shell.env("TBOT_SUBSHELL_TEST", "INNERMOST")
                assert linux_shell.env("TBOT_SUBSHELL_TEST") == "INNERMOST"
            assert linux_shell.env("TBOT_SUBSHELL_TEST") == "SECOND_PLACE"
        assert linux_shell.env("TBOT_SUBSHELL_TEST") == "NUMBER_ONE"


def test_simple_control(any_linux_shell: AnyLinuxShell) -> None:
    with any_linux_shell() as linux_shell:
        out = linux_shell.exec0(
            "false", linux.AndThen, "echo", "FOO", linux.OrElse, "echo", "BAR"
        ).strip()
        assert out == "BAR"

        out = linux_shell.exec0(
            "true", linux.AndThen, "echo", "FOO", linux.OrElse, "echo", "BAR"
        ).strip()
        assert out == "FOO"


def test_simple_jobs(any_linux_shell: AnyLinuxShell) -> None:
    with any_linux_shell() as linux_shell:
        import re
        import time

        t1 = time.monotonic()
        out = linux_shell.exec0(
            "sleep", "infinity", linux.Background, "echo", "Hello World"
        ).strip()
        t2 = time.monotonic()
        pid = linux_shell.env("!")

        assert re.match(r"\[\d+\] \d+\nHello World", out), repr(out)
        assert (
            t2 - t1
        ) < 9.0, f"Command took {t2 - t1}s (max 9s). Sleep was not sent to background"

        # Kill the sleep process.  In some circumstances, tbot does not
        # seem to be able to kill all child processes of a subprocess
        # channel.  To prevent this from leading to issues, kill the sleep
        # right here instead of relying on tbot to do so correctly at the
        # very end.      Tracking-Issue: Rahix/tbot#13
        linux_shell.exec("kill", pid, linux.Then, "wait", pid)


def test_background_jobs(any_linux_shell: AnyLinuxShell) -> None:
    with any_linux_shell() as linux_shell:
        f1 = linux_shell.workdir / "bg1.txt"
        f2 = linux_shell.workdir / "bg2.txt"
        out = linux_shell.exec0(
            "echo",
            "foo",
            linux.Background(stdout=f1),
            "echo",
            "bar",
            linux.Background(stdout=f2, stderr=f2),
            "wait",
        )
        out = f1.read_text().strip()
        assert out == "foo"
        out = f2.read_text().strip()
        assert out == "bar"
