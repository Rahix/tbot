import typing
import tbot
from tbot.machine import linux


@tbot.testcase
def test_lab(lab: typing.Optional[linux.Lab] = None,) -> None:
    with lab or tbot.acquire_lab() as lh:
        p = lh.workdir / "foobar"

        lh.exec0("echo", p)


@tbot.testcase
def test_linux(mach: typing.Optional[linux.LinuxMachine] = None,) -> None:
    with mach or tbot.acquire_lab() as lnx:
        p = lnx.workdir / "foobar"

        with tbot.acquire_lab() as lh:
            p2 = lh.workdir / "barfoo"

            # Should fail!
            lnx.exec0("echo", p2)
            lh.exec0("echo", p)

            with tbot.acquire_board(lh) as b:
                with tbot.acquire_linux(b) as lnx2:
                    p3 = lnx2.workdir / "barbarbar"

                    # Should fail!
                    lh.exec0("echo", p3)
                    lnx.exec0("echo", p3)
                    lnx2.exec0("echo", p)
                    lnx2.exec0("echo", p2)

                    # Should pass!
                    lnx.exec0("echo", p)
                    lh.exec0("echo", p2)
                    lnx2.exec0("echo", p3)
