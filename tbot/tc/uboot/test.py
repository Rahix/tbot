import tbot
from tbot.machine import board


@tbot.named_testcase("uboot_smoke_test")
@tbot.with_uboot
def smoke_test(ub: board.UBootShell) -> None:
    ub.exec0("version")
    ub.exec0("bdinfo")
    ub.exec0("printenv")
