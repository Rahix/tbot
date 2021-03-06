import pytest

from tbot.machine import linux
from conftest import AnyLinuxShell


def test_run_working(any_linux_shell: AnyLinuxShell) -> None:
    with any_linux_shell() as linux_shell:
        with linux_shell.run("bash", "--norc", "--noprofile") as bs:
            bs.sendline("exit")
            bs.terminate0()


def test_run_working_text(any_linux_shell: AnyLinuxShell) -> None:
    with any_linux_shell() as linux_shell:
        f = linux_shell.workdir / "test_run.txt"
        with linux_shell.run("cat", linux.RedirStdout(f)) as cat:
            cat.sendline("Hello World")
            cat.sendline("Lorem ipsum")

            cat.sendcontrol("D")
            cat.terminate0()

        with linux_shell.run("cat", f) as cat:
            content = cat.terminate0()

        assert content == "Hello World\nLorem ipsum\n"


def test_failing_use_after_terminate(any_linux_shell: AnyLinuxShell) -> None:
    with any_linux_shell() as linux_shell:
        with linux_shell.run("cat") as cat:
            cat.sendcontrol("D")
            cat.terminate0()

            with pytest.raises(linux.CommandEndedException):
                cat.sendline("Hello World")

            with pytest.raises(Exception):
                cat.terminate0()


def test_failing_unexpected_abort(any_linux_shell: AnyLinuxShell) -> None:
    with any_linux_shell() as linux_shell:
        with linux_shell.run("echo", "Hello World", linux.Then, "false") as echo:
            with pytest.raises(linux.CommandEndedException):
                echo.read_until_prompt("Lorem Ipsum")

            with pytest.raises(linux.CommandEndedException):
                echo.sendline("Hello World")

            retcode, _ = echo.terminate()
            assert retcode == 1, "Did not capture retcode of early exiting command"


def test_failing_bad_retcode(any_linux_shell: AnyLinuxShell) -> None:
    with any_linux_shell() as linux_shell:
        with pytest.raises(Exception):
            with linux_shell.run("false") as false:
                false.terminate0()

        with linux_shell.run("sh", "-c", "exit 123") as sh:
            rc = sh.terminate()[0]
            assert rc == 123, f"Expected return code 123, got {rc}"


def test_failing_no_terminate(any_linux_shell: AnyLinuxShell) -> None:
    with any_linux_shell() as linux_shell:
        with pytest.raises(RuntimeError):
            with linux_shell.run("echo", "Hello World"):
                pass

        # Necessary to bring machine back into good state
        linux_shell.ch.read_until_prompt()
        linux_shell.exec0("true")
