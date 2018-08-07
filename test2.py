import tbot
from tbot.machine import linux


@tbot.testcase
def foo_bar() -> None:
    with tbot.acquire_lab() as lh:
        lh.exec0("lsb_release", "-a")


@tbot.testcase
def test_imports() -> None:
    with tbot.acquire_lab() as lh:
        path = linux.Path(lh, "/tmp")

        lh.exec0("ls", path)
        lh.exec0("readlink", "-f", lh.workdir)

        with tbot.acquire_board(lh) as bd:
            with tbot.acquire_uboot(bd) as ub:
                ub.tmp_cmd("version")
                tbot.log.message(f"{ub!r}")


if __name__ == "__main__":
    test_imports()
