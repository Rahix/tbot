import tbot
from tbot.machine import linux


@tbot.testcase
def cat_file(f: linux.Path) -> str:
    return f.host.exec0("cat", f)


@tbot.testcase
def test_devel() -> None:
    from config.labs import dummy
    with dummy.DummyLabSSH() as lh:
        tbot.log.message(f"Host: {lh!r}")
        v = cat_file(linux.Path(lh, "/proc/version")).strip()
        tbot.log.message(f"Version: {v}")

        f = linux.Path(lh, lh.workdir / "myfile.txt")
        lh.exec0("uname", "-n", stdout=f)

        name = cat_file(f).strip()
        tbot.log.message(f"Name: {name}")

    try:
        class MyException(Exception):
            pass

        @tbot.testcase
        def failing() -> None:
            raise MyException()

        failing()
    except MyException:
        pass


@tbot.testcase
def test_board() -> None:
    from config.labs import dummy as dummy_lab
    from config.boards import dummy as dummy_board
    with dummy_lab.DummyLabLocal() as lh:
        with dummy_board.DummyBoard(lh) as bd:
            with dummy_board.DummyBoardUBoot(bd) as b:
                b.tmp_cmd("echo Hello")
                b.tmp_cmd("version")
                b.tmp_cmd("printenv bootcmd")


@tbot.testcase
def test_ev() -> None:
    from tbot import log
    ev = log.EventIO()
    ev.write("Hello World\nFoo")
    ev.write(" Bar\nHello World")


if __name__ == "__main__":
    test_board()
