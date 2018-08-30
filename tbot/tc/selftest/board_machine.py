import typing
import tbot
from tbot.machine import channel
from tbot.machine import linux
from tbot.machine import board


class TestBoard(board.Board):
    name = "test"

    def poweron(self) -> None:
        self.lh.exec0("touch", self.lh.workdir / "selftest_power")

    def poweroff(self) -> None:
        self.lh.exec0("rm", self.lh.workdir / "selftest_power")

    def connect(self) -> channel.Channel:
        return self.lh.new_channel(
            linux.Raw(
                """\
sh; exit
PS1='Test-U-Boot> '
alias version="uname -a"
alias printenv="set | grep -E '^U'"
sh
read -p 'Autoboot: '"""
            )
        )


class TestBoardUBoot(board.UBootMachine[TestBoard]):
    autoboot_prompt = "Autoboot: "
    prompt = "Test-U-Boot> "


@tbot.testcase
def selftest_board_uboot(lab: typing.Optional[tbot.selectable.LabHost] = None,) -> None:
    with lab or tbot.acquire_lab() as lh:
        b_: board.Board
        try:
            b_ = tbot.acquire_board(lh)
        except RuntimeError:
            b_ = TestBoard(lh)
        with b_ as b:
            ub_: board.UBootMachine
            if isinstance(b, tbot.selectable.Board):
                ub_ = tbot.acquire_uboot(b)
            elif isinstance(b, TestBoard):
                ub_ = TestBoardUBoot(b)
            with ub_ as ub:
                ub.exec0("version")
                env = ub.exec0("printenv").strip().split("\n")

                for line in env[:-1]:
                    if line != "" and line[0].isalnum():
                        assert "=" in line, line


@tbot.testcase
def selftest_board_power(lab: typing.Optional[tbot.selectable.LabHost] = None,) -> None:
    with lab or tbot.acquire_lab() as lh:
        power_path = lh.workdir / "selftest_power"
        if power_path.exists():
            lh.exec0("rm", power_path)

        tbot.log.message("Emulating a normal run ...")
        assert not power_path.exists()
        with TestBoard(lh):
            assert power_path.exists()

        assert not power_path.exists()

        class TestException(Exception):
            pass

        tbot.log.message("Emulating a failing run ...")
        try:
            with TestBoard(lh):
                assert power_path.exists()
                tbot.log.message("raise TestException()")
                raise TestException()
        except TestException:
            pass

        assert not power_path.exists()
