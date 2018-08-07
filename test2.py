import tbot
from tbot.machine import linux


@tbot.testcase
def test_imports() -> None:
    with tbot.acquire_lab() as lh:
        path = linux.Path(lh, "/tmp")

        lh.exec0("ls", path)
        lh.exec0("readlink", "-f", lh.workdir)


if __name__ == "__main__":
    test_imports()
