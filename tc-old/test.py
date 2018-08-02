import typing
import signal
import tbot
from tbot import tc  # noqa: tbot.tc


def handler(_signum: typing.Any, _frame: typing.Any) -> None:
    """ Signal handler for timeout """
    raise TimeoutError()


@tbot.testcase
def test_buildhost(tb: tbot.TBot) -> None:
    ubdir = tb.call("uboot_checkout", clean=False)
    tb.call("retrive_build_artifact", buildfile=ubdir / "u-boot.bin")


@tbot.testcase
def test_config_error(tb: tbot.TBot) -> None:
    tb.config["uboot.shell.nonexsistent-key"]


@tbot.testcase
def test_bad_ssh(tb: tbot.TBot) -> None:
    with tb.machine(tbot.machine.MachineBuild(
        name="custom_fail",
        ssh_command="ssh nobody@nonexistant-host",
    )) as tb:
        raise Exception("We cannot get here if everything works ...")


@tbot.testcase
def test_return_after_interactive(tb: tbot.TBot) -> None:
    with tb.with_board_uboot() as tb:
        tb.call("interactive_uboot")

        vers = tb.boardshell.exec0("version")
        assert vers.startswith("U-Boot")


@tbot.testcase
def test_params(tb: tbot.TBot, oblig: bool, opt: bool = False) -> None:
    """ Test parameters """
    tbot.log.message(f"Oblig: {oblig}\nOptio: {opt}")


@tbot.testcase
def test_bad_commands(tb: tbot.TBot) -> None:
    def cmd(tb: tbot.TBot, cmd: str, success: bool) -> None:
        raised = False
        try:
            with tb.machine(tbot.machine.MachineLabEnv()) as tb:
                tbot.log.debug(f"Testing {cmd!r}")

                signal.alarm(1)
                tb.shell.exec(cmd)
                signal.alarm(0)

                tb.call("selftest_env_shell")
        except BaseException as e:
            tbot.log.debug(f"Catched {e!r}")
            raised = True
        assert raised is not success

    signal.signal(signal.SIGALRM, handler)
    tb.call(cmd, cmd="exit", success=False)
    tb.call(cmd, cmd="\x04", success=False)

    tb.call(cmd, cmd="\n", success=False)
    tb.call(cmd, cmd="echo 1\necho 2", success=False)


@tbot.testcase
def test_clogs(tb: tbot.TBot) -> None:
    tb.shell.exec0("echo NOENV")

    with tb.machine(tbot.machine.MachineLabEnv()) as tb:
        tb.shell.exec0("echo ENV")

    with tb.with_board_uboot() as tb:
        tb.boardshell.exec0("echo U-Boot")

    with tb.with_board_linux() as tb:
        tb.boardshell.exec0("echo Linux")


@tbot.testcase
def test_exception(tb: tbot.TBot) -> None:
    raise tbot.InvalidUsageException("failed a testcase, bummer!\nfoor")
