import typing
import tbot
from tbot.machine import channel
from tbot.machine import linux
from tbot.machine import board


class TestBoard(board.Board):
    """Dummy Board."""

    name = "test"

    def poweron(self) -> None:  # noqa: D102
        self.lh.exec0("touch", self.lh.workdir / "selftest_power")

    def poweroff(self) -> None:  # noqa: D102
        self.lh.exec0("rm", self.lh.workdir / "selftest_power")

    def connect(self) -> channel.Channel:  # noqa: D102
        return self.lh.new_channel(
            linux.Raw(
                """\
bash --norc; exit
unset HISTFILE
PS1='Test-U-Boot> '
alias version="uname -a"
alias printenv="set | grep -E '^U'"
bash --norc
unset HISTFILE
set +o emacs
set +o vi
read -p 'Autoboot: '"""
            )
        )


class TestBoardUBoot(board.UBootMachine[TestBoard]):
    """Dummy Board UBoot."""

    autoboot_prompt = "Autoboot: "
    prompt = "Test-U-Boot> "


@tbot.testcase
def selftest_board_uboot(lab: typing.Optional[tbot.selectable.LabHost] = None) -> None:
    """Test if TBot intercepts U-Boot correctly."""
    with lab or tbot.acquire_lab() as lh:
        b_: board.Board
        try:
            b_ = tbot.acquire_board(lh)
        except NotImplementedError:
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
def selftest_board_linux(lab: typing.Optional[tbot.selectable.LabHost] = None) -> None:
    """Test board's linux."""
    with lab or tbot.acquire_lab() as lh:
        try:
            b_ = tbot.acquire_board(lh)
        except NotImplementedError:
            tbot.log.message(
                tbot.log.c("Skipped").yellow.bold + " because no board available."
            )
            return
        with b_ as b:
            with tbot.acquire_linux(b) as lnx:
                from . import machine as mach

                mach.selftest_machine_shell(lnx)


@tbot.testcase
def selftest_board_power(lab: typing.Optional[tbot.selectable.LabHost] = None) -> None:
    """Test if the board is powered on and off correctly."""
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


class TestBoardLinuxUB(board.LinuxWithUBootMachine[TestBoard]):
    """Dummy board linux uboot."""

    uboot = TestBoardUBoot
    boot_commands = [
        ["echo", "Booting linux ..."],
        ["echo", "[  0.000]", "boot: message"],
        ["echo", "[  0.013]", "boot: info"],
        ["echo", "[  0.157]", "boot: message"],
        [
            board.Raw(
                "printf 'tb-login: '; read username; printf 'Password: '; read password; [[ $username = 'root' && $password = 'rootpw' ]] || exit 1"
            )
        ],
    ]

    username = "root"
    password = "rootpw"
    login_prompt = "tb-login: "
    login_wait = 0.02


@tbot.testcase
def selftest_board_linux_uboot(
    lab: typing.Optional[tbot.selectable.LabHost] = None
) -> None:
    """Test linux booting from U-Boot."""
    with lab or tbot.acquire_lab() as lh:
        tbot.log.message("Testing without UB ...")
        with TestBoard(lh) as b:
            with TestBoardLinuxUB(b) as lnx:
                lnx.exec0("uname", "-a")

        tbot.log.message("Testing with UB ...")
        with TestBoard(lh) as b:
            with TestBoardUBoot(b) as ub:
                with TestBoardLinuxUB(ub) as lnx:
                    lnx.exec0("uname", "-a")


@tbot.testcase
def selftest_board_linux_nopw(
    lab: typing.Optional[tbot.selectable.LabHost] = None
) -> None:
    """Test linux without a password."""

    class TestBoardLinuxUB_NOPW(board.LinuxWithUBootMachine[TestBoard]):
        uboot = TestBoardUBoot
        boot_commands = [
            ["echo", "Booting linux ..."],
            ["echo", "[  0.000]", "boot: message"],
            ["echo", "[  0.013]", "boot: info"],
            ["echo", "[  0.157]", "boot: message"],
            [
                board.Raw(
                    "printf 'tb-login: '; read username; [[ $username = 'root' ]] || exit 1"
                )
            ],
        ]

        username = "root"
        password = None
        login_prompt = "tb-login: "
        login_wait = 0.02

    with lab or tbot.acquire_lab() as lh:
        tbot.log.message("Testing without UB ...")
        with TestBoard(lh) as b:
            with TestBoardLinuxUB_NOPW(b) as lnx:
                lnx.exec0("uname", "-a")

        tbot.log.message("Testing with UB ...")
        with TestBoard(lh) as b:
            with TestBoardUBoot(b) as ub:
                with TestBoardLinuxUB_NOPW(ub) as lnx:
                    lnx.exec0("uname", "-a")


@tbot.testcase
def selftest_board_linux_standalone(
    lab: typing.Optional[tbot.selectable.LabHost] = None
) -> None:
    """Test linux booting standalone."""

    class TestBoardLinuxStandalone(board.LinuxStandaloneMachine[TestBoard]):
        username = "root"
        password = None
        login_prompt = "Autoboot: "
        login_wait = 0.02

    with lab or tbot.acquire_lab() as lh:
        tbot.log.message("Testing without UB ...")
        with TestBoard(lh) as b:
            with TestBoardLinuxStandalone(b) as lnx:
                lnx.exec0("uname", "-a")

        tbot.log.message("Testing with UB ...")
        with TestBoard(lh) as b:
            with TestBoardUBoot(b) as ub:
                raised = False
                try:
                    with TestBoardLinuxStandalone(ub) as lnx:
                        lnx.exec0("uname", "-a")
                except RuntimeError:
                    raised = True
                assert raised
