import pytest
import testmachines

import tbot
from tbot.machine import board


def test_board_power(tbot_context: tbot.Context) -> None:
    with tbot_context.request(tbot.role.LabHost) as lh:
        tbot_context.teardown_if_alive(testmachines.MockhwBoardLinux)
        tbot_context.teardown_if_alive(testmachines.MockhwBoardUBoot)
        tbot_context.teardown_if_alive(testmachines.MockhwBoard)

        power_path = lh.workdir / "mockhw-power-status"
        assert not power_path.exists()

        with tbot_context.request(testmachines.MockhwBoard, exclusive=True):
            assert power_path.read_text() == "on"

        assert not power_path.exists()


def test_uboot_simple_commands(tbot_context: tbot.Context) -> None:
    with tbot_context.request(testmachines.MockhwBoardUBoot) as ub:
        ub.exec0("version")
        assert ub.exec0("echo", "Hello World") == "Hello World\n"
        assert ub.exec0("echo", "$?", "!#") == "$? !#\n"


def test_uboot_long_output(tbot_context: tbot.Context) -> None:
    with tbot_context.request(testmachines.MockhwBoardUBoot) as ub:
        s = "_".join(map(lambda i: f"{i:02}", range(80)))
        assert ub.exec0("echo", s) == f"{s}\n"


def test_uboot_return_code(tbot_context: tbot.Context) -> None:
    with tbot_context.request(testmachines.MockhwBoardUBoot) as ub:
        assert ub.test("true")
        assert not ub.test("false")


def test_uboot_simple_environment(tbot_context: tbot.Context) -> None:
    with tbot_context.request(testmachines.MockhwBoardUBoot) as ub:
        value = "12 foo !? # true; exit"
        ub.env("tbot_test_env_var", value)
        assert ub.env("tbot_test_env_var") == value


def test_uboot_simple_control(tbot_context: tbot.Context) -> None:
    with tbot_context.request(testmachines.MockhwBoardUBoot) as ub:
        out = ub.exec0(
            "false", board.AndThen, "echo", "FOO", board.OrElse, "echo", "BAR"
        ).strip()
        assert out == "BAR"

        out = ub.exec0(
            "true", board.AndThen, "echo", "FOO", board.OrElse, "echo", "BAR"
        ).strip()
        assert out == "FOO"


def test_linux_boot(tbot_context: tbot.Context) -> None:
    with tbot_context.request(testmachines.MockhwBoardLinux) as lnx:
        out = lnx.exec0("echo", "Hello World")
        assert out == "Hello World\n"

        out = lnx.exec0("echo", "$?", "!#")
        assert out == "$? !#\n"

        with pytest.raises(tbot.error.CommandFailure):
            lnx.exec0("false")
