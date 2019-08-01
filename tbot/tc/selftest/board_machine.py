import contextlib
import re
import typing

import tbot
from tbot.machine import channel, linux, board, connector
from . import machine as mach


class DummyConnector(connector.Connector):
    def __init__(self, mach: linux.LinuxShell, autoboot: bool = True) -> None:
        self.mach = mach
        self.autoboot = autoboot

    @contextlib.contextmanager
    def _connect(self) -> typing.Iterator[channel.Channel]:
        with self.mach.clone() as cloned:
            ch = cloned.ch.take()
            tbot.log_event.command(self.mach.name, "dummy-connect")
            if self.autoboot:
                ch.sendline(
                    """\
bash --norc --noediting; exit
unset HISTFILE
PS1='Test-U-Boot> '
alias version="uname -a"
function printenv() {
    if [ $# = 0 ]; then
        set | grep -E '^U'
    else
        set | grep "$1" | sed "s/'//g"
    fi
}
function setenv() { local var="$1"; shift; eval "$var=\\"$*\\""
}
bash --norc --noediting""",
                    read_back=True,
                )
                ch.sendline(
                    """\
unset HISTFILE
set +o emacs
set +o vi
read -p 'Autoboot: '; exit""",
                    read_back=True,
                )
            else:
                ch.sendline(
                    """\
bash --norc --noediting; exit
unset HISTFILE
alias version="uname -a"
function printenv() {
    if [ $# = 0 ]; then
        set | grep -E '^U'
    else
        set | grep "$1" | sed "s/'//g"
    fi
}
function setenv() { local var="$1"; shift; eval "$var=\\"$*\\""
}
PS1=Test-U-Boot'> ' #""",
                    read_back=True,
                )

            yield ch

    def clone(self) -> typing.NoReturn:
        raise NotImplementedError("can't clone a serial connection")


class TestBoard(board.Board):
    """Dummy Board."""


class TestUBoot(DummyConnector, board.UBootAutobootIntercept, board.UBootShell):
    """Dummy Board UBoot."""

    name = "test-ub"

    autoboot_prompt = re.compile(b"Autoboot: ")
    prompt = "Test-U-Boot> "


class TestBoardUBoot:
    pass


@tbot.testcase
def selftest_board_uboot(lab: typing.Optional[tbot.selectable.LabHost] = None) -> None:
    """Test if tbot intercepts U-Boot correctly."""

    with contextlib.ExitStack() as cx:
        lh = cx.enter_context(lab or tbot.acquire_lab())
        try:
            ub: board.UBootShell = cx.enter_context(tbot.acquire_uboot(lh))
        except NotImplementedError:
            ub = cx.enter_context(TestUBoot(lh))

        ub.exec0("version")
        env = ub.exec0("printenv").strip().split("\n")

        for line in env[:-1]:
            if line != "" and line[0].isalnum():
                assert "=" in line, repr(line)

        out = ub.exec0("echo", hex(0x1234)).strip()
        assert out == "0x1234", repr(out)

        mach.selftest_machine_shell(ub)


@tbot.testcase
def selftest_board_uboot_noab(
    lab: typing.Optional[tbot.selectable.LabHost] = None
) -> None:
    """Test if tbot intercepts U-Boot correctly without autoboot."""

    class TestUBootNoAB(DummyConnector, board.UBootShell):
        """Dummy Board UBoot."""

        name = "test-ub-noab"

        prompt = "Test-U-Boot> "

    with contextlib.ExitStack() as cx:
        lh = cx.enter_context(lab or tbot.acquire_lab())
        ub = cx.enter_context(TestUBootNoAB(lh, autoboot=False))

        ub.exec0("version")
        env = ub.exec0("printenv").strip().split("\n")

        for line in env[:-1]:
            if line != "" and line[0].isalnum():
                assert "=" in line, repr(line)

        out = ub.exec0("echo", hex(0x1234)).strip()
        assert out == "0x1234", repr(out)

        mach.selftest_machine_shell(ub)


@tbot.testcase
def selftest_board_linux(lab: typing.Optional[tbot.selectable.LabHost] = None) -> None:
    """Test board's linux."""

    tbot.log.skip("board-linux")
    return

    with contextlib.ExitStack() as cx:
        lh = cx.enter_context(lab or tbot.acquire_lab())

        try:
            b = cx.enter_context(tbot.acquire_board(lh))
        except NotImplementedError:
            tbot.log.message(
                tbot.log.c("Skipped").yellow.bold + " because no board available."
            )
            return

        lnx = cx.enter_context(tbot.acquire_linux(b))

        mach.selftest_machine_shell(lnx)


@tbot.testcase
def selftest_board_power(lab: typing.Optional[tbot.selectable.LabHost] = None) -> None:
    """Test if the board is powered on and off correctly."""

    class TestPowerUBoot(
        DummyConnector,
        board.PowerControl,
        board.UBootAutobootIntercept,
        board.UBootShell,
    ):
        """Dummy Board UBoot."""

        name = "test-ub-power"

        autoboot_prompt = re.compile(b"Autoboot: ")
        prompt = "Test-U-Boot> "

        def poweron(self) -> None:
            self.mach.exec0("touch", self.mach.workdir / "selftest_power")

        def poweroff(self) -> None:
            self.mach.exec0("rm", self.mach.workdir / "selftest_power")

    with lab or tbot.acquire_lab() as lh:
        power_path = lh.workdir / "selftest_power"
        if power_path.exists():
            lh.exec0("rm", power_path)

        tbot.log.message("Emulating a normal run ...")
        assert not power_path.exists()
        with TestPowerUBoot(lh):
            assert power_path.exists()

        assert not power_path.exists()

        class TestException(Exception):
            pass

        tbot.log.message("Emulating a failing run ...")
        try:
            with TestPowerUBoot(lh):
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
    shell = linux.shell.Bash

    @property
    def workdir(self) -> "linux.Path[TestBoardLinuxUB]":  # type: ignore
        """Return workdir."""
        raise NotImplementedError("workdir")
        # return linux.Workdir.static(self, "/tmp/tbot-wd")


@tbot.testcase
def selftest_board_linux_uboot(
    lab: typing.Optional[tbot.selectable.LabHost] = None
) -> None:
    """Test linux booting from U-Boot."""

    tbot.log.skip("board-linux & u-boot")
    return

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
                    lnx.exec0("ls", lnx.workdir)


@tbot.testcase
def selftest_board_linux_nopw(
    lab: typing.Optional[tbot.selectable.LabHost] = None
) -> None:
    """Test linux without a password."""

    tbot.log.skip("board-linux nopw")
    return

    class TestBoardLinuxUB_NOPW(board.LinuxWithUBootMachine[TestBoard]):
        uboot = TestBoardUBoot
        boot_commands = [
            ["echo", "Booting linux ..."],
            ["echo", "[  0.000]", "boot: message"],
            ["echo", "[  0.013]", "boot: info"],
            ["echo", "[  0.157]", "boot: message"],
            ["export", "HOME=/tmp"],
            [
                board.Raw(
                    "printf 'tb-login: '; read username; [[ $username = 'root' ]] || exit 1"
                )
            ],
        ]

        username = "root"
        password = None
        login_prompt = "tb-login: "
        shell = linux.shell.Bash

        @property
        def workdir(self) -> "linux.Path[TestBoardLinuxUB_NOPW]":  # type: ignore
            """Return workdir."""
            return linux.Workdir.athome(self, "tbot-wd")

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
                    lnx.exec0("ls", lnx.workdir)


@tbot.testcase
def selftest_board_linux_standalone(
    lab: typing.Optional[tbot.selectable.LabHost] = None
) -> None:
    """Test linux booting standalone."""

    tbot.log.skip("board-linux standalone")
    return

    class TestBoardLinuxStandalone(board.LinuxStandaloneMachine[TestBoard]):
        username = "root"
        password = None
        login_prompt = "Autoboot: "
        shell = linux.shell.Bash

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


@tbot.testcase
def selftest_board_linux_bad_console(
    lab: typing.Optional[tbot.selectable.LabHost] = None
) -> None:
    """Test linux booting standalone."""

    tbot.log.skip("board-linux bad console")
    return

    class BadBoard(TestBoard):
        def connect(self) -> channel.Channel:  # noqa: D102
            return self.lh.new_channel(
                linux.Raw(
                    """\
bash --norc --noediting; exit
PS1="$"
unset HISTFILE
export UNAME="bad-board"
bash --norc --noediting
PS1=""
unset HISTFILE
set +o emacs
set +o vi
echo ""
echo "[0.127] We will go into test mode now ..."
echo "[0.128] Let's see if I can behave bad enough to break you"
read -p 'bad-board login: [0.129] No clean login prompt for you';\
sleep 0.02;\
echo "[0.1337] Oh you though it was this easy?";\
read -p "Password: [0.ORLY?] Password ain't clean either you fool
It's even worse tbh";\
sleep 0.02;\
echo "[0.512] I have one last trick >:|";\
sleep 0.2;\
read -p ""\
"""
                )
            )

    class BadBoardLinux(board.LinuxStandaloneMachine[BadBoard]):
        username = "root"
        password = "toor"
        shell = linux.shell.Bash

    with lab or tbot.acquire_lab() as lh:
        with BadBoard(lh) as b:
            with BadBoardLinux(b) as lnx:
                name = lnx.env("UNAME")
                assert name == "bad-board", repr(name)
