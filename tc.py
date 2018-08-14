import typing
import tbot


@tbot.testcase
def uname(
    lh: typing.Optional[tbot.machine.linux.LinuxMachine] = None,
) -> None:
    with lh or tbot.acquire_lab() as lh:
        lh.exec0("uname", "-a")
