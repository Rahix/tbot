import typing
import tbot
from tbot.machine_v2 import linux, connector

__all__ = (
    "selftest_machinev2_reentrant",
)


def tmp_lab() -> linux.LinuxShell:
    class TempLab(
        connector.SubprocessConnector,
        linux.Bash,
    ):
        name = "temp-lab"

    return TempLab()


@tbot.testcase
def selftest_machinev2_reentrant(lab: typing.Optional[linux.LinuxShell] = None,) -> None:
    """Test if a machine can be entered multiple times."""
    with lab or tmp_lab() as lh:
        with lh as h1:
            h1.exec0("export", "_TBOT=111")
            assert h1.exec0("printenv", "_TBOT") == "111\r\n"

        with lh as h2:
            assert h2.exec0("printenv", "_TBOT") == "111\r\n"


@tbot.testcase
def selftest_machinev2_shell(lab: typing.Optional[linux.LinuxShell] = None) -> None:
    with lab or tmp_lab() as m:
        tbot.log.message("Testing command output ...")
        out = m.exec0("echo", "Hello World")
        assert out == "Hello World\r\n", repr(out)

        out = m.exec0("echo", "$?", "!#")
        assert out == "$? !#\r\n", repr(out)

        out = m.exec0("printf", "Hello World")
        assert out == "Hello World", repr(out)

        out = m.exec0("printf", "Hello\\nWorld")
        assert out == "Hello\r\nWorld", repr(out)

        # Broken
        if False:
            out = m.exec0("printf", "Hello\nWorld")
            assert out == "Hello\nWorld", repr(out)

        s = "_".join(map(lambda i: f"{i:02}", range(80)))
        out = m.exec0("echo", s)
        assert out == f"{s}\r\n", repr(out)

        tbot.log.message("Testing return codes ...")
        assert m.test("true")
        assert not m.test("false")

        tbot.log.message("Testing control flow ...")
        out = m.exec0(
            "false", linux.AndThen, "echo", "FOO", linux.OrElse, "echo", "BAR"
        ).strip()
        assert out == "BAR", repr(out)

        out = m.exec0(
            "true", linux.AndThen, "echo", "FOO", linux.OrElse, "echo", "BAR"
        ).strip()
        assert out == "FOO", repr(out)

        tbot.log.message("Testing env vars ...")
        value = "12 - foo !? # true; exit"
        m.env("TBOT_TEST_ENV_VAR", value)
        out = m.env("TBOT_TEST_ENV_VAR")
        assert out == value, repr(out)
